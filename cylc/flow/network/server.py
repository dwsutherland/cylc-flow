# THIS FILE IS PART OF THE CYLC WORKFLOW ENGINE.
# Copyright (C) NIWA & British Crown (Met Office) & Contributors.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""Server for workflow runtime API."""

import getpass  # noqa: F401
from textwrap import dedent
from threading import Barrier

from graphql.execution.executors.asyncio import AsyncioExecutor
import zmq
from zmq.auth.thread import ThreadAuthenticator

from cylc.flow import LOG, workflow_files
from cylc.flow.cfgspec.glbl_cfg import glbl_cfg
from cylc.flow.network.authorisation import authorise
from cylc.flow.network.graphql import (
    CylcGraphQLBackend, IgnoreFieldMiddleware, instantiate_middleware
)
from cylc.flow.network.publisher import WorkflowPublisher
from cylc.flow.network.replier import WorkflowReplier
from cylc.flow.network.resolvers import Resolvers
from cylc.flow.network.schema import schema
from cylc.flow.data_store_mgr import DELTAS_MAP
from cylc.flow.data_messages_pb2 import PbEntireWorkflow  # type: ignore

# maps server methods to the protobuf message (for client/UIS import)
PB_METHOD_MAP = {
    'pb_entire_workflow': PbEntireWorkflow,
    'pb_data_elements': DELTAS_MAP
}


def expose(func=None):
    """Expose a method on the sever."""
    func.exposed = True
    return func


def filter_none(dictionary):
    """Filter out `None` items from a dictionary:

    Examples:
        >>> filter_none({
        ...     'a': 0,
        ...     'b': '',
        ...     'c': None
        ... })
        {'a': 0, 'b': ''}

    """
    return {
        key: value
        for key, value in dictionary.items()
        if value is not None
    }


class WorkflowRuntimeServer:
    """Workflow runtime service API facade exposed via zmq.

    This class contains the Cylc endpoints.

    Args:
        schd (object): The parent object instantiating the server. In
            this case, the workflow scheduler.
        context (object): The instantiated ZeroMQ context (i.e. zmq.Context())
            passed in from the application.
        barrier (object): Threading Barrier object used to sync threads, for
            the main thread to ensure socket setup has finished.

    Usage:
        * Define endpoints using the ``expose`` decorator.
        * Call endpoints using the function name.

    Message interface:
        * Accepts requests of the format: {"command": CMD, "args": {...}}
        * Returns responses of the format: {"data": {...}}
        * Returns error in the format: {"error": {"message": MSG}}

    Common Arguments:
        Arguments which are shared between multiple commands.

        task identifier (str):
            A task identifier in the format ``task.cycle-point``
            e.g. ``foo.1`` or ``bar.20000101T0000Z``.

        .. _task globs:

        task globs (list):
            A list of strings in the format
            ``name[.cycle_point][:task_state]`` where ``name`` could be a
            task or family name.

             Glob-like patterns may be used to match multiple items e.g.

             ``*``
                Matches everything.
             ``*.1``
                Matches everything in cycle ``1``.
             ``*.*:failed``
                Matches all failed tasks.

    """

    def __init__(self, schd):

        self.zmq_context = None
        self.port = None
        self.pub_port = None
        self.replier = None
        self.publisher = None
        self.barrier = None
        self.curve_auth = None
        self.client_pub_key_dir = None

        self.schd = schd
        self.public_priv = None  # update in get_public_priv()
        self.endpoints = None
        self.resolvers = Resolvers(
            self.schd.data_store_mgr,
            schd=self.schd
        )
        self.middleware = [
            IgnoreFieldMiddleware,
        ]

    def configure(self):
        self.register_endpoints()
        # create thread sync barrier for setup
        self.barrier = Barrier(3, timeout=10)

        # TODO: this in zmq asyncio context?
        # Requires the scheduler main loop in asyncio first
        # And use of concurrent.futures.ThreadPoolExecutor?
        self.zmq_context = zmq.Context()
        # create an authenticator for the ZMQ context
        self.curve_auth = ThreadAuthenticator(self.zmq_context, log=LOG)
        self.curve_auth.start()  # start the authentication thread

        # Setting the location means that the CurveZMQ auth will only
        # accept public client certificates from the given directory, as
        # generated by a user when they initiate a ZMQ socket ready to
        # connect to a server.
        workflow_srv_dir = workflow_files.get_workflow_srv_dir(
            self.schd.workflow)
        client_pub_keyinfo = workflow_files.KeyInfo(
            workflow_files.KeyType.PUBLIC,
            workflow_files.KeyOwner.CLIENT,
            workflow_srv_dir=workflow_srv_dir)
        self.client_pub_key_dir = client_pub_keyinfo.key_path

        # Initial load for the localhost key.
        self.curve_auth.configure_curve(
            domain='*',
            location=(self.client_pub_key_dir)
        )

        self.replier = WorkflowReplier(
            self, context=self.zmq_context, barrier=self.barrier)
        self.publisher = WorkflowPublisher(
            self.schd.workflow, context=self.zmq_context, barrier=self.barrier)

    async def start(self):
        """Start the TCP servers."""
        port_range = glbl_cfg().get(['scheduler', 'run hosts', 'ports'])
        self.replier.start(port_range[0], port_range[-1])
        self.publisher.start(port_range[0], port_range[-1])
        # wait for threads to setup socket ports before continuing
        self.barrier.wait()
        self.port = self.replier.port
        self.pub_port = self.publisher.port
        self.schd.data_store_mgr.delta_workflow_ports()

    async def stop(self, reason):
        """Stop the TCP servers, and clean up authentication."""
        if self.replier:
            self.replier.stop()
        if self.publisher:
            await self.publisher.publish(
                [(b'shutdown', str(reason).encode('utf-8'))]
            )
            self.publisher.stop()
        self.curve_auth.stop()  # stop the authentication thread

    def responder(self, message):
        """Process message, coordinate publishing, return response."""
        # TODO: coordinate publishing.
        return self._receiver(message)

    def _receiver(self, message):
        """Wrap incoming messages and dispatch them to exposed methods.

        Args:
            message (dict): message contents
        """
        # determine the server method to call
        try:
            method = getattr(self, message['command'])
            args = message['args']
            args.update({'user': message['user']})
            if 'meta' in message:
                args['meta'] = message['meta']
        except KeyError:
            # malformed message
            return {'error': {
                'message': 'Request missing required field(s).'}}
        except AttributeError:
            # no exposed method by that name
            return {'error': {
                'message': 'No method by the name "%s"' % message['command']}}

        # generate response
        try:
            response = method(**args)
        except Exception as exc:
            # includes incorrect arguments (TypeError)
            LOG.exception(exc)  # note the error server side
            import traceback
            return {'error': {
                'message': str(exc), 'traceback': traceback.format_exc()}}

        return {'data': response}

    def register_endpoints(self):
        """Register all exposed methods."""
        self.endpoints = {name: obj
                          for name, obj in self.__class__.__dict__.items()
                          if hasattr(obj, 'exposed')}

    @authorise()
    @expose
    def api(self, endpoint=None):
        """Return information about this API.

        Returns a list of callable endpoints.

        Args:
            endpoint (str, optional):
                If specified the documentation for the endpoint
                will be returned instead.

        Returns:
            list/str: List of endpoints or string documentation of the
            requested endpoint.

        """
        if not endpoint:
            return [
                method for method in dir(self)
                if getattr(getattr(self, method), 'exposed', False)
            ]

        try:
            method = getattr(self, endpoint)
        except AttributeError:
            return 'No method by name "%s"' % endpoint
        if method.exposed:
            head, tail = method.__doc__.split('\n', 1)
            tail = dedent(tail)
            return '%s\n%s' % (head, tail)
        return 'No method by name "%s"' % endpoint

    @authorise()
    @expose
    def graphql(self, request_string=None, variables=None):
        """Return the GraphQL scheme execution result.

        Args:
            request_string (str, optional):
                GraphQL request passed to Graphene
            variables (dict, optional):
                Dict of variables passed to Graphene

        Returns:
            object: Execution result, or a list with errors.
        """
        try:
            executed = schema.execute(
                request_string,
                variable_values=variables,
                context={
                    'resolvers': self.resolvers,
                },
                backend=CylcGraphQLBackend(),
                middleware=list(instantiate_middleware(self.middleware)),
                executor=AsyncioExecutor(),
                validate=True,  # validate schema (dev only? default is True)
                return_promise=False,
            )
        except Exception as exc:
            return 'ERROR: GraphQL execution error \n%s' % exc
        if executed.errors:
            errors = []
            for error in executed.errors:
                if hasattr(error, '__traceback__'):
                    import traceback
                    errors.append({'error': {
                        'message': str(error),
                        'traceback': traceback.format_exception(
                            error.__class__, error, error.__traceback__)}})
                    continue
                errors.append(getattr(error, 'message', None))
            return errors
        return executed.data

    @authorise()
    @expose
    def get_graph_raw(self, start_point_string, stop_point_string,
                      group_nodes=None, ungroup_nodes=None,
                      ungroup_recursive=False, group_all=False,
                      ungroup_all=False):
        """Return a textural representation of the workflow graph.

        .. warning::

           The grouping options:

           * ``group_nodes``
           * ``ungroup_nodes``
           * ``group_all``
           * ``ungroup_all``

           Are mutually exclusive.

        Args:
            start_point_string (str):
                Cycle point as a string to define the window of view of the
                workflow graph.
            stop_point_string (str):
                Cycle point as a string to define the window of view of the
                workflow graph.
            group_nodes (list, optional):
                List of (graph nodes) family names to group (collapse according
                to inheritance) in the output graph.
            ungroup_nodes (list, optional):
                List of (graph nodes) family names to ungroup (expand according
                to inheritance) in the output graph.
            ungroup_recursive (bool, optional):
                Recursively ungroup families.
            group_all (bool, optional):
                Group all families (collapse according to inheritance).
            ungroup_all (bool, optional):
                Ungroup all families (expand according to inheritance).

        Returns:
            list: [left, right, None, is_suicide, condition]

            left (str):
                Task identifier for the dependency of
                an edge.
            right (str):
                Task identifier for the dependant task
                of an edge.
            is_suicide (bool):
                True if edge represents a suicide trigger.
            condition:
                Conditional expression if edge represents a conditional trigger
                else ``None``.

        """
        # Ensure that a "None" str is converted to the None value.
        return self.schd.info_get_graph_raw(
            start_point_string, stop_point_string,
            group_nodes=group_nodes,
            ungroup_nodes=ungroup_nodes,
            ungroup_recursive=ungroup_recursive,
            group_all=group_all,
            ungroup_all=ungroup_all)

    # UIServer Data Commands
    @authorise()
    @expose
    def pb_entire_workflow(self):
        """Send the entire data-store in a single Protobuf message.

        Returns:
            bytes
                Serialised Protobuf message

        """
        pb_msg = self.schd.data_store_mgr.get_entire_workflow()
        return pb_msg.SerializeToString()

    @authorise()
    @expose
    def pb_data_elements(self, element_type):
        """Send the specified data elements in delta form.

        Args:
            element_type (str):
                Key from DELTAS_MAP dictionary.

        Returns:
            bytes
                Serialised Protobuf message

        """
        pb_msg = self.schd.data_store_mgr.get_data_elements(element_type)
        return pb_msg.SerializeToString()
