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

### Query Related ###

## Field args (i.e. for queries etc):
job_args = dict(
    ids=graphene.List(graphene.ID, default_value=[]),
    exids=graphene.List(graphene.ID, default_value=[]),
    states=graphene.List(graphene.String, default_value=[]),
    exstates=graphene.List(graphene.String, default_value=[]))

tree_args = dict(
    ids=graphene.List(graphene.ID, default_value=[]),
    exids=graphene.List(graphene.ID, default_value=[]),
    states=graphene.List(graphene.String, default_value=[]),
    exstates=graphene.List(graphene.String, default_value=[]),
    mindepth=graphene.Int(default_value=-1),
    maxdepth=graphene.Int(default_value=-1))

## Resolvers:
def get_suite_info(root, info):
    schd = info.context.get('schd_obj')
    return schd.info_get_global_data()

def get_nodes(root, info, **args):
    """Resolver for returning job, task, family nodes"""
    field_name = to_snake_case(info.field_name)
    field_ids = getattr(root, field_name, None)
    if field_ids:
        args['ids'] = field_ids
    elif field_ids == []:
        return []
    schd = info.context.get('schd_obj')
    node_type = str(info.return_type.of_type).replace('!','')
    return schd.info_get_nodes(args, n_type=node_type)

def get_node(root, info, **args):
    """Resolver for returning job, task, family node"""
    field_name = to_snake_case(info.field_name)
    field_ids = getattr(root, field_name, None)
    if field_ids:
        args['ids'] = [field_ids]
    elif field_ids == []:
        return []
    schd = info.context.get('schd_obj')
    node_type = str(info.return_type).replace('!','')
    return schd.info_get_node(args, n_type=node_type)

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

class QLSuite(graphene.ObjectType):
    """Global suite info."""
    class Meta:
        default_resolver = dict_resolver
    api_version = graphene.Int()
    cylc_version = graphene.String()
    host = graphene.String()
    job_log_names = graphene.List(graphene.String)
    last_updated = graphene.Float()
    meta = graphene.Field(QLMeta)
    namespace_definition_order = graphene.List(graphene.String)
    newest_runahead_cycle_point = graphene.String()
    newest_cycle_point = graphene.String()
    oldest_cycle_point = graphene.String()
    owner = graphene.String()
    reloading = graphene.Boolean()
    run_mode = graphene.String()
    state_totals = graphene.Field(QLStateTotals)
    states = graphene.List(graphene.String)
    status = graphene.String()
    suite = graphene.String(required=True)
    suite_log_dir = graphene.String()
    time_zone_info = graphene.Field(QLTimeZone)
    tree_depth = graphene.Int()

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
    batch_sys_job_id = graphene.ID()
    batch_sys_name = graphene.String()
    batch_sys_conf = GenericScalar(default_value={})
    directives = GenericScalar(default_value={})
    environment = GenericScalar(default_value={})
    env_script = graphene.String()
    err_script = graphene.String()
    exit_script = graphene.String()
    extra_logs = graphene.List(graphene.String)
    execution_time_limit = graphene.Float()
    finished_time = graphene.Float()
    finished_time_string = graphene.String()
    host = graphene.String()
    init_script = graphene.String()
    job_log_dir = graphene.String()
    owner = graphene.String()
    param_env_tmpl = GenericScalar(default_value={})
    param_var = GenericScalar(default_value={})
    post_script = graphene.String()
    pre_script = graphene.String()
    script = graphene.String()
    shell = graphene.String()
    started_time = graphene.Float()
    started_time_string = graphene.String()
    state = graphene.String()
    submit_num = graphene.Int()
    submitted_time = graphene.Float()
    submitted_time_string = graphene.String()
    task_proxy = graphene.Field(
        lambda: QLTaskProxy,
        description="""Associated Task Proxy""",
        required=True,
        resolver=get_node)
    work_sub_dir = graphene.String()

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
        args = tree_args,
        resolver=get_nodes)

class QLCondition(graphene.ObjectType):
    """Prerequisite conditions."""
    task_id = graphene.ID(required=True)
    task_proxy = graphene.Field(
        lambda: QLTaskProxy,
        description="""Associated Task Proxy""",
        resolver=get_node)
    expr_alias = graphene.String()
    req_state = graphene.String()
    satisfied = graphene.Boolean()
    message = graphene.String()

class QLPrerequisite(graphene.ObjectType):
    """Task prerequisite."""
    expression = graphene.String()
    conditions = graphene.List(
        QLCondition,
        description="""Condition monomers of a task prerequisites.""")
    cycle_points = graphene.List(graphene.String)
    satisfied = graphene.Boolean()

class QLTaskProxy(graphene.ObjectType):
    """Task Cycle Specific info"""
    id = graphene.ID(required=True)
    broadcasts = GenericScalar(default_value={})
    cycle_point = graphene.String()
    depth = graphene.Int()
    job_submits = graphene.Int()
    latest_message = graphene.String()
    namespace = graphene.List(graphene.String,required=True)
    outputs = graphene.Field(QLOutputs)
    prerequisites = graphene.List(QLPrerequisite)
    spawned = graphene.Boolean()
    state = graphene.String()
    jobs = graphene.List(
        QLJob,
        description="""Task jobs.""",
        args = job_args,
        resolver=get_nodes)
    parents = graphene.List(
        lambda: QLFamilyProxy,
        description="""Task parents.""",
        args = tree_args,
        resolver=get_nodes)
    task = graphene.Field(
        QLTask,
        description="""Task definition""",
        required=True,
        resolver=get_node)

class QLFamily(graphene.ObjectType):
    """Task definition, static fields"""
    id = graphene.ID(required=True)
    name = graphene.String(required=True)
    meta = graphene.Field(QLMeta)
    depth = graphene.Int()
    proxies = graphene.List(
        lambda: QLFamilyProxy,
        description="""Associated cycle point proxies""",
        args = tree_args,
        resolver=get_nodes)
    parents = graphene.List(
        lambda: QLFamily,
        description="""Family definition parent.""",
        args = tree_args,
        resolver=get_nodes)
    child_tasks = graphene.List(
        QLTask,
        description="""Descendedant definition tasks.""",
        args = tree_args,
        resolver=get_nodes)
    child_families = graphene.List(
        lambda: QLFamily,
        description="""Descendedant desc families.""",
        args = tree_args,
        resolver=get_nodes)

class QLFamilyProxy(graphene.ObjectType):
    """Family composite."""
    id = graphene.ID(required=True)
    family = graphene.Field(
        QLFamily,
        description="""Family definition""",
        required=True,
        resolver=get_node)
    cycle_point = graphene.String()
    state = graphene.String()
    depth = graphene.Int()
    parents = graphene.List(
        lambda: QLFamilyProxy,
        description="""Family parent proxies.""",
        args = tree_args,
        resolver=get_nodes)
    child_tasks = graphene.List(
        QLTaskProxy,
        description="""Descendedant task proxies.""",
        args = tree_args,
        resolver=get_nodes)
    child_families = graphene.List(
        lambda: QLFamilyProxy,
        description="""Descendedant family proxies.""",
        args = tree_args,
        resolver=get_nodes)

## Query declaration
class Query(graphene.ObjectType):
    suite_info = graphene.Field(
        QLSuite,
        resolver=get_suite_info)
    jobs = graphene.List(
        QLJob,
        args = job_args,
        resolver=get_nodes)
    tasks = graphene.List(
        QLTask,
        args = tree_args,
        resolver=get_nodes)
    task_proxies = graphene.List(
        QLTaskProxy,
        args = tree_args,
        resolver=get_nodes)
    families = graphene.List(
        QLFamily,
        args = tree_args,
        resolver=get_nodes)
    family_proxies = graphene.List(
        QLFamilyProxy,
        args = tree_args,
        resolver=get_nodes)


### Mutation Related ###
## Mutations Types:
class Broadcast(graphene.Mutation):
    class Meta:
        description = """Clear, Expire, or Put a broadcast:
- Clear settings globally, or for listed namespaces and/or points
- Expire all settings targeting cycle points earlier than cutoff.
- Put up new broadcast settings (server side interface)."""
    class Arguments:
        action = graphene.String(
            description="""String options:
- put
- clear
- expire""",
            required=True,)
        points = graphene.List(
            graphene.String,
            description="""points: ["*"]""",)
        namespaces = graphene.List(
            graphene.String,
            description="""namespaces: ["foo", "BAZ"]""",)
        settings = graphene.List(
            GenericScalar,
            description="""
settings: [{envronment: {ENVKEY: "env_val"}}, ...]""",)

    modified_settings = GenericScalar()
    bad_options = GenericScalar()

    def mutate(self, info, action, points=[], namespaces=[], settings=[]):
        schd = info.context.get('schd_obj')
        broadcast_mgr = schd.task_events_mgr.broadcast_mgr
        mod_ret=[]
        if action == 'put':
            mod_ret, bad_ret = broadcast_mgr.put_broadcast(
            points, namespaces, settings)
        elif action == 'clear':
            mod_ret, bad_ret = broadcast_mgr.clear_broadcast(
            points, namespaces, settings)
        elif action == 'expire':
            if points:
                cutoff = points[0]
                mod_ret, bad_ret = broadcast_mgr.expire_broadcast(cutoff)
        else:
            bad_ret = {'action': action}
        return Broadcast(modified_settings=mod_ret, bad_options=bad_ret)

class StopSuite(graphene.Mutation):
    class Meta:
        description = """Stop the suite:
- Cleanly or after kill active tasks.
- After cycle point.
- On event handler completion, or terminate right away.
- After an instance of a task."""
    class Arguments:
        stop_type = graphene.String(
            description="""String options:
- cleanly
- clock_time
- now
- task""",
            required=True,)
        items = graphene.List(graphene.String,
            description="""List of String(s):
- after_clock_time: ISO 8601 compatible or YYYY/MM/DD-HH:mm
- after_task: task ID(s)""",)
        actions = GenericScalar(
            description="""String boolean pairs:
- kill_active_tasks:  True/False
- terminate:  True/False""",)

    command_queued = graphene.Boolean()

    def mutate(self, info, stop_type, items=[], actions={}):
        if stop_type in ['now']:
            stop_cmd = 'stop_now'
        elif stop_type in ['clean']:
            stop_cmd = 'set_stop_cleanly'
        else:
            stop_cmd = 'set_stop_after_' + stop_type
        stop_items = ()
        for val in items:
            stop_items += (val,)
        schd = info.context.get('schd_obj')
        schd.command_queue.put((stop_cmd,stop_items,actions))
        return StopSuite(command_queued=True)

## Mutation declarations
class Mutation(graphene.ObjectType):
    broadcast = Broadcast.Field(
        description=Broadcast._meta.description)
    stop_suite = StopSuite.Field(
        description=StopSuite._meta.description)


schema = graphene.Schema(query=Query, mutation=Mutation)

