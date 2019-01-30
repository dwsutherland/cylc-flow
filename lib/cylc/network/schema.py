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
from graphene.utils.str_converters import to_snake_case

## Resolvers:
def get_nodes(root, info, **args):
    """Resolver for returning job, task, family nodes"""
    field_name = to_snake_case(info.field_name)
    field_items = getattr(root, field_name, None)
    if field_items:
        args['items'] = field_items
    elif field_items == []:
            return []
    schd = info.context.get('schd_obj')
    return schd.info_get_nodes(args, n_type=str(info.return_type.of_type))

def get_node(root, info, **args):
    """Resolver for returning job, task, family nodes"""
    field_name = to_snake_case(info.field_name)
    field_id = getattr(root, field_name, None)
    if field_id:
        args['id'] = field_id
    schd = info.context.get('schd_obj')
    return schd.info_get_node(args, n_type=str(info.return_type.of_type))

## Types:
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
    suite = graphene.String(required=True)
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

class QLTask(graphene.ObjectType):
    """Task definition, static fields"""
    id = graphene.ID(required=True)
    name = graphene.String(required=True)
    meta = graphene.Field(QLMeta)
    mean_elapsed_time = graphene.Float()
    namespace = graphene.List(graphene.String,required=True)
    depth = graphene.Int()
    proxies = graphene.List(
        lambda: QLTaskProxy,
        description="""Associated cycle point proxies""",
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

class QLOutputs(graphene.ObjectType):
    """Task State Outputs"""
    expired = graphene.Boolean()
    submitted = graphene.Boolean()
    submit_failed = graphene.Boolean()
    started = graphene.Boolean()
    succeeded = graphene.Boolean()
    failed = graphene.Boolean()

class QLJob(graphene.ObjectType):
    """Jobs."""
    id = graphene.ID(required=True)
    state = graphene.String()
    host = graphene.String()
    submit_num = graphene.Int()
    submit_method_id = graphene.ID()
    batch_sys_name = graphene.String()
    submitted_time = graphene.Float()
    started_time = graphene.Float()
    finished_time = graphene.Float()
    submitted_time_string = graphene.String()
    started_time_string = graphene.String()
    finished_time_string = graphene.String()
    execution_time_limit = graphene.Float()
    logfiles = graphene.List(graphene.String)
    outputs = graphene.Field(QLOutputs)
    task_proxy = graphene.List(
        lambda: QLTaskProxy,
        description="""Associated Task Proxy""",
        resolver=get_node
        )

class QLPrereq(graphene.ObjectType):
    """Task prerequisite."""
    condition = graphene.String()
    message = graphene.String()

class QLTask(graphene.ObjectType):
    """Task definition, static fields"""
    id = graphene.ID(required=True)
    name = graphene.String(required=True)
    meta = graphene.Field(QLMeta)
    mean_elapsed_time = graphene.Float()
    namespace = graphene.List(graphene.String,required=True)
    depth = graphene.Int()
    proxies = graphene.List(
        lambda: QLTaskProxy,
        description="""Associated cycle point proxies""",
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

class QLTaskProxy(graphene.ObjectType):
    """Task Cycle Specific info"""
    id = graphene.ID(required=True)
    task = graphene.Field(
        QLTask,
        description="""Task definition""",
        required=True,
        resolver=get_node
        )
    cycle_point = graphene.String()
    state = graphene.String()
    spawned = graphene.Boolean()
    latest_message = graphene.String()
    prerequisites = graphene.List(QLPrereq)
    job_submits = graphene.Int()
    namespace = graphene.List(graphene.String,required=True)
    depth = graphene.Int()
    jobs = graphene.List(
        QLJob,
        description="""Task jobs.""",
        id=graphene.ID(default_value=None),
        exid=graphene.ID(default_value=None),
        items=graphene.List(graphene.ID, default_value=[]),
        exitems=graphene.List(graphene.ID, default_value=[]),
        states=graphene.List(graphene.String, default_value=[]),
        exstates=graphene.List(graphene.String, default_value=[]),
        mindepth=graphene.Int(default_value=-1),
        maxdepth=graphene.Int(default_value=-1),
        resolver=get_node
        )
    parents = graphene.List(
        lambda: QLFamilyProxy,
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

class QLFamily(graphene.ObjectType):
    """Task definition, static fields"""
    id = graphene.ID(required=True)
    name = graphene.String(required=True)
    meta = graphene.Field(QLMeta)
    depth = graphene.Int()
    proxies = graphene.List(
        lambda: QLFamilyProxy,
        description="""Associated cycle point proxies""",
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
    parents = graphene.List(
        lambda: QLFamily,
        description="""Family definition parent.""",
        id=graphene.ID(default_value=None),
        exid=graphene.ID(default_value=None),
        items=graphene.List(graphene.ID, default_value=[]),
        exitems=graphene.List(graphene.ID, default_value=[]),
        depth=graphene.Int(default_value=-1),
        mindepth=graphene.Int(default_value=-1),
        maxdepth=graphene.Int(default_value=-1),
        resolver=get_nodes
        )
    child_tasks = graphene.List(
        QLTask,
        description="""Descendedant definition tasks.""",
        id=graphene.ID(default_value=None),
        exid=graphene.ID(default_value=None),
        items=graphene.List(graphene.ID, default_value=[]),
        exitems=graphene.List(graphene.ID, default_value=[]),
        mindepth=graphene.Int(default_value=-1),
        maxdepth=graphene.Int(default_value=-1),
        resolver=get_nodes
        )
    child_families = graphene.List(
        lambda: QLFamily,
        description="""Descendedant desc families.""",
        id=graphene.ID(default_value=None),
        exid=graphene.ID(default_value=None),
        items=graphene.List(graphene.ID, default_value=[]),
        exitems=graphene.List(graphene.ID, default_value=[]),
        mindepth=graphene.Int(default_value=-1),
        maxdepth=graphene.Int(default_value=-1),
        resolver=get_nodes
        )

class QLFamilyProxy(graphene.ObjectType):
    """Family composite."""
    id = graphene.ID(required=True)
    family = graphene.Field(
        QLFamily,
        description="""Family definition""",
        required=True,
        resolver=get_node
        )
    cycle_point = graphene.String()
    state = graphene.String()
    depth = graphene.Int()
    parents = graphene.List(
        lambda: QLFamilyProxy,
        description="""Family parent proxies.""",
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
    child_tasks = graphene.List(
        QLTaskProxy,
        description="""Descendedant task proxies.""",
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
    child_families = graphene.List(
        lambda: QLFamilyProxy,
        description="""Descendedant family proxies.""",
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

class Query(graphene.ObjectType):
    globalInfo = graphene.Field(QLGlobal)
    tasks = graphene.List(
        QLTask,
        id=graphene.ID(default_value=None),
        exid=graphene.ID(default_value=None),
        items=graphene.List(graphene.ID, default_value=[]),
        exitems=graphene.List(graphene.ID, default_value=[]),
        mindepth=graphene.Int(default_value=-1),
        maxdepth=graphene.Int(default_value=-1),
        resolver=get_nodes
        )
    task_proxies = graphene.List(
        QLTaskProxy,
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
        mindepth=graphene.Int(default_value=-1),
        maxdepth=graphene.Int(default_value=-1),
        resolver=get_nodes
        )
    family_proxies = graphene.List(
        QLFamilyProxy,
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

    def resolve_globalInfo(self, info):
        schd = info.context.get('schd_obj')
        return schd.info_get_global_data()


schema = graphene.Schema(query=Query)

