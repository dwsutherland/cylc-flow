#!/usr/bin/env python2

# THIS FILE IS PART OF THE CYLC SUITE ENGINE.
# Copyright (C) 2008-2018 NIWA & British Crown (Met Office) & Contributors.
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
"""GraphQL API schema via Graphene implementation."""


import graphene
from graphene import relay
from graphene.types.resolver import dict_resolver

from cylc.task_outputs import (
    TASK_OUTPUT_EXPIRED, TASK_OUTPUT_SUBMITTED, TASK_OUTPUT_SUBMIT_FAILED,
    TASK_OUTPUT_STARTED, TASK_OUTPUT_SUCCEEDED, TASK_OUTPUT_FAILED)


class QLPrereq(graphene.ObjectType):
    """Task prerequisite."""
    condition = graphene.String()
    message = graphene.String()


class QLJobHost(graphene.ObjectType):
    """Task job host."""
    submit_num = graphene.Int()
    job_host = graphene.String()


class QLOutputs(graphene.ObjectType):
    """Task State Outputs"""
    expired = graphene.Boolean()
    submitted = graphene.Boolean()
    submit_failed = graphene.Boolean()
    started = graphene.Boolean()
    succeeded = graphene.Boolean()
    failed = graphene.Boolean()


class QLTask(graphene.ObjectType):
    """Task composite."""
    class Meta:
        interfaces = (relay.Node,)

    name = graphene.String()
    label = graphene.String()
    state = graphene.String()
    title = graphene.String()
    description = graphene.String()
    URL = graphene.String()
    spawned = graphene.Boolean()
    execution_time_limit = graphene.Float()
    submitted_time = graphene.Float()
    started_time = graphene.Float()
    finished_time = graphene.Float()
    mean_elapsed_time = graphene.Float()
    submitted_time_string = graphene.String()
    started_time_string = graphene.String()
    finished_time_string = graphene.String()
    host = graphene.String()
    batch_sys_name = graphene.String()
    submit_method_id = graphene.String()
    submit_num = graphene.Int()
    logfiles = graphene.List(graphene.String)
    latest_message = graphene.String()
    job_hosts = graphene.List(QLJobHost)
    prerequisites = graphene.List(QLPrereq)
    outputs = graphene.Field(QLOutputs)

    @classmethod
    def get_node(cls, info, id):
        schd = info.context.get('schd_obj')
        args={'id': id}
        result = schd.info_graphql_tasks(args)
        return result[0]

class TaskConnection(relay.Connection):
    class Meta:
        node = QLTask


class Query(graphene.ObjectType):
    node = relay.Node.Field()
    hello = graphene.String(name=graphene.String(default_value="stranger"))
    apiversion = graphene.Int()
    tasks = relay.ConnectionField(
        TaskConnection,
        id=graphene.ID(default_value=None),
        states=graphene.List(graphene.String, default_value=[]),
    )

    def resolve_hello(self, info, name):
        return 'Hello ' + name

    def resolve_apiversion(self, info):
        return info.context.get('app_server').config['CYLC_API']

    def resolve_tasks(self, info, **args):
        schd = info.context.get('schd_obj')
        return schd.info_graphql_tasks(args)


schema = graphene.Schema(query=Query)

