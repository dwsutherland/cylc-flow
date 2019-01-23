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
from graphene.types.resolver import dict_resolver
from graphene.types.generic import GenericScalar


def get_nodes(root, info, **args):
    """Resolver for returning job, task, family nodes"""
    type_obj_name = str(info.return_type.of_type)
    if type_obj_name == 'QLTask':
        ntype = 'task'
    if type_obj_name == 'QLFamily':
        ntype = 'family'
    if hasattr(root, info.field_name):
        args['items'] = getattr(root, info.field_name)
        if not args['items']:
            return []
    schd = info.context.get('schd_obj')
    return schd.info_get_graphql_nodes(args, node_type=ntype)

class QLMeta(graphene.ObjectType):
    """Meta data fields, and custom fields generic userdefined dump"""
    class Meta:
        default_resolver = dict_resolver
    title = graphene.String(default_value=None)
    description = graphene.String(default_value=None)
    URL = graphene.String(default_value=None)
    user_defined = GenericScalar(default_value={})

class QLTimeZone(graphene.ObjectType):
    """Time zone info."""
    class Meta:
        default_resolver = dict_resolver
    hours = graphene.Int()
    string_basic = graphene.String()
    string_extended = graphene.String()
    minutes = graphene.Int()

class QLStateTotals(graphene.ObjectType):
    """State Totals."""
    class Meta:
        default_resolver = dict_resolver
    runahead = graphene.Int()
    waiting = graphene.Int()
    held = graphene.Int()
    queued = graphene.Int()
    expired = graphene.Int()
    ready = graphene.Int()
    submit_failed = graphene.Int()
    submit_retrying = graphene.Int()
    submitted = graphene.Int()
    retrying = graphene.Int()
    running = graphene.Int()
    failed = graphene.Int()
    succeeded = graphene.Int()

class QLGlobal(graphene.ObjectType):
    """Global suite info."""
    class Meta:
        default_resolver = dict_resolver
    suite = graphene.String()
    owner = graphene.String()
    host = graphene.String()
    meta = graphene.Field(QLMeta)
    reloading = graphene.Boolean()
    time_zone_info = graphene.Field(QLTimeZone)
    last_updated = graphene.Float()
    status = graphene.String()
    state_totals = graphene.Field(QLStateTotals)
    states = graphene.List(graphene.String)
    run_mode = graphene.String()
    namespace_definition_order = graphene.List(graphene.String)
    newest_runahead_cycle_point = graphene.String()
    newest_cycle_point = graphene.String()
    oldest_cycle_point = graphene.String()
    tree_depth = graphene.Int()


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
    """Task unitary."""
    id = graphene.ID()
    name = graphene.String()
    cycle_point = graphene.String()
    state = graphene.String()
    meta = graphene.Field(QLMeta)
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
    namespace = graphene.List(graphene.String)
    logfiles = graphene.List(graphene.String)
    latest_message = graphene.String()
    job_hosts = graphene.List(QLJobHost)
    prerequisites = graphene.List(QLPrereq)
    outputs = graphene.Field(QLOutputs)
    parents = graphene.List(
        lambda: QLFamily,
        description="""Task parents.""",
        id=graphene.ID(default_value=None),
        exid=graphene.ID(default_value=None),
        items=graphene.List(graphene.ID, default_value=[]),
        exitems=graphene.List(graphene.ID, default_value=[]),
        states=graphene.List(graphene.String, default_value=[]),
        exstates=graphene.List(graphene.String, default_value=[]),
        mindepth=graphene.Int(default_value=-1),
        maxdepth=graphene.Int(default_value=-1),
        resolver=get_nodes
        )
    node_depth = graphene.Int()


class QLFamily(graphene.ObjectType):
    """Family composite."""
    id = graphene.ID()
    name = graphene.String()
    cycle_point = graphene.String()
    state = graphene.String()
    meta = graphene.Field(QLMeta)
    parents = graphene.List(
        lambda: QLFamily,
        description="""Family parents.""",
        id=graphene.ID(default_value=None),
        exid=graphene.ID(default_value=None),
        items=graphene.List(graphene.ID, default_value=[]),
        exitems=graphene.List(graphene.ID, default_value=[]),
        states=graphene.List(graphene.String, default_value=[]),
        exstates=graphene.List(graphene.String, default_value=[]),
        depth=graphene.Int(default_value=-1),
        mindepth=graphene.Int(default_value=-1),
        maxdepth=graphene.Int(default_value=-1),
        resolver=get_nodes
        )
    tasks = graphene.List(
        lambda: QLTask,
        description="""Desendedant tasks.""",
        id=graphene.ID(default_value=None),
        exid=graphene.ID(default_value=None),
        items=graphene.List(graphene.ID, default_value=[]),
        exitems=graphene.List(graphene.ID, default_value=[]),
        states=graphene.List(graphene.String, default_value=[]),
        exstates=graphene.List(graphene.String, default_value=[]),
        mindepth=graphene.Int(default_value=-1),
        maxdepth=graphene.Int(default_value=-1),
        resolver=get_nodes
        )
    families = graphene.List(
        lambda: QLFamily,
        description="""Desendedant families.""",
        id=graphene.ID(default_value=None),
        exid=graphene.ID(default_value=None),
        items=graphene.List(graphene.ID, default_value=[]),
        exitems=graphene.List(graphene.ID, default_value=[]),
        states=graphene.List(graphene.String, default_value=[]),
        exstates=graphene.List(graphene.String, default_value=[]),
        mindepth=graphene.Int(default_value=-1),
        maxdepth=graphene.Int(default_value=-1),
        resolver=get_nodes
        )
    node_depth = graphene.Int()



class Query(graphene.ObjectType):
    apiversion = graphene.Int(required=True)
    globalInfo = graphene.Field(QLGlobal)
    tasks = graphene.List(
        QLTask,
        id=graphene.ID(default_value=None),
        exid=graphene.ID(default_value=None),
        items=graphene.List(graphene.ID, default_value=[]),
        exitems=graphene.List(graphene.ID, default_value=[]),
        states=graphene.List(graphene.String, default_value=[]),
        exstates=graphene.List(graphene.String, default_value=[]),
        mindepth=graphene.Int(default_value=-1),
        maxdepth=graphene.Int(default_value=-1),
        resolver=get_nodes
        )
    families = graphene.List(
        QLFamily,
        id=graphene.ID(default_value=None),
        exid=graphene.ID(default_value=None),
        items=graphene.List(graphene.ID, default_value=[]),
        exitems=graphene.List(graphene.ID, default_value=[]),
        states=graphene.List(graphene.String, default_value=[]),
        exstates=graphene.List(graphene.String, default_value=[]),
        mindepth=graphene.Int(default_value=-1),
        maxdepth=graphene.Int(default_value=-1),
        resolver=get_nodes
        )

    def resolve_apiversion(self, info):
        return info.context.get('app_server').config['API']

    def resolve_globalInfo(self, info):
        schd = info.context.get('schd_obj')
        return schd.info_get_graphql_global()



schema = graphene.Schema(query=Query)

