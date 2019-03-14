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
    port = graphene.Int()
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
    outputs = GenericScalar()
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
## Mutations defined:
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

class HoldSuite(graphene.Mutation):
    class Meta:
        description = """Hold items/suite:
- set hold on suite.
- Set hold point of suite."""
    class Arguments:
        hold_type = graphene.String(
            description="""String options:
- hold_suite
- hold_after_point_string""",
            required=True,)
        point_string = graphene.String()
    command_queued = graphene.Boolean()
    def mutate(self, info, hold_type, point_string=None):
        schd = info.context.get('schd_obj')
        item_tuple = ()
        if point_string is not None:
            item_tuple = (point_string,)
        schd.command_queue.put((hold_type, item_tuple, {}))
        return HoldSuite(command_queued=True)

class NudgeSuite(graphene.Mutation):
    class Meta:
        description = """Tell suite to try task processing."""
    command_queued = graphene.Boolean()
    def mutate(self, info):
        schd = info.context.get('schd_obj')
        schd.command_queue.put(("nudge", (), {}))
        return NudgeSuite(command_queued=True)

class PutMessages(graphene.Mutation):
    class Meta:
        description = """Put task messages in queue for processing
later by the main loop."""
    class Arguments:
        job_id = graphene.String(
            description="""Task job in the form "CYCLE/TASK_NAME/SUBMIT_NUM""",
            required=True)
        event_time = graphene.String(required=True)
        messages = graphene.List(
            graphene.List(graphene.String, required=True),
            description="""List in the form [[severity, message], ...].""")
    messages_queued = graphene.String()
    def mutate(self, info, job_id, event_time, messages):
        schd = info.context.get('schd_obj')
        for severity, message in messages:
            schd.message_queue.put((job_id, event_time, severity, message))
        return PutMessages(messages_queued='%d' % len(messages))

class ReleaseSuite(graphene.Mutation):
    class Meta:
        description = """Tell suite to reload the suite definition."""
    command_queued = graphene.Boolean()
    def mutate(self, info):
        schd = info.context.get('schd_obj')
        schd.command_queue.put(("release_suite", (), {}))
        return ReleaseSuite(command_queued=True)

class ReloadSuite(graphene.Mutation):
    class Meta:
        description = """Tell suite to reload the suite definition."""
    command_queued = graphene.Boolean()
    def mutate(self, info):
        schd = info.context.get('schd_obj')
        schd.command_queue.put(("reload_suite", (), {}))
        return ReloadSuite(command_queued=True)

class SetVerbosity(graphene.Mutation):
    class Meta:
        description = """Set suite verbosity to new level."""
    class Arguments:
        level = graphene.String(
            description="""levels:
INFO, WARNING, NORMAL, CRITICAL, ERROR, DEBUG""",
            required=True)
    command_queued = graphene.Boolean()
    def mutate(self, info, level):
        schd = info.context.get('schd_obj')
        schd.command_queue.put(("set_verbosity", (level,), {}))
        return SetVerbosity(command_queued=True)

class StopSuiteArgs(graphene.InputObjectType):
    kill_active_tasks = graphene.Boolean(description="""Use with:
- set_stop_cleanly""")
    Terminate = graphene.Boolean(description="""Use with:
- stop_now""")

class StopSuite(graphene.Mutation):
    class Meta:
        description = """Suite stop actions:
- Cleanly or after kill active tasks.
- After cycle point.
- On event handler completion, or terminate right away.
- After an instance of a task."""
    class Arguments:
        action = graphene.String(
            description="""String options:
- set_stop_cleanly
- set_stop_after_clock_time
- set_stop_after_task
- stop_now""",
            required=True,)
        item = graphene.String(
            description="""Stop items:
- after_clock_time: ISO 8601 compatible or YYYY/MM/DD-HH:mm
- after_task: task ID""",)
        args = StopSuiteArgs()
    command_queued = graphene.Boolean()
    def mutate(self, info, action, item=None, args={}):
        schd = info.context.get('schd_obj')
        item_tuple = ()
        if item is not None:
            item_tuple = (item,)
        schd.command_queue.put((action, item_tuple, args))
        return StopSuite(command_queued=True)

class TaskArgs(graphene.InputObjectType):
    check_syntax = graphene.Boolean(description="""Use with actions:
- dry_run_tasks""")
    no_check = graphene.Boolean(description="""Use with actions:
- insert_tasks""")
    stop_point_string = graphene.String(description="""Use with actions:
- insert_tasks""")
    poll_succ = graphene.Boolean(description="""Use with actions:
- poll_tasks""")
    spawn = graphene.Boolean(description="""Use with actions:
- remove_tasks""")
    state = graphene.String(description="""Use with actions:
- reset_task_states""")
    outputs = graphene.List(graphene.String,description="""Use with actions:
- reset_task_states""")
    back_out = graphene.Boolean(description="""Use with actions:
- trigger_tasks""")

class TaskActions(graphene.Mutation):
    class Meta:
        description = """Task actions:
- Prepare job file for task(s).
- Hold tasks.
- Insert task proxies.
- Kill task jobs.
- Return True if task_id exists (and running).
- Unhold tasks.
- Remove tasks from task pool.
- Reset statuses tasks.
- Spawn tasks.
- Trigger submission of task jobs where possible."""
    class Arguments:
        action = graphene.String(
            description = """Task actions:
- dry_run_tasks
- hold_tasks
- insert_tasks
- kill_tasks
- poll_tasks
- release_tasks
- remove_tasks
- reset_task_states
- spawn_tasks
- trigger_tasks""",
            required=True,)
        items = graphene.List(
            graphene.String,
            description="""
A list of identifiers (family/glob/id) for matching task proxies, i.e.
["foo.201901*:failed", "201901*/baa:failed", "FAM.20190101T0000Z", "FAM2",
    "*.20190101T0000Z"]
""",
            required=True,)
        args = TaskArgs()
    command_queued = graphene.Boolean()
    def mutate(self, info, action, items, args={}):
        schd = info.context.get('schd_obj')
        schd.command_queue.put((action, (items,), args))
        return TaskActions(command_queued=True)

class TakeCheckpoint(graphene.Mutation):
    class Meta:
        description = """Checkpoint current task pool."""
    class Arguments:
        items = graphene.List(
            graphene.String,
            description="""items[0] used as checkpoint event name).""",
            required=True,)
    command_queued = graphene.Boolean()
    def mutate(self, info, items):
        schd = info.context.get('schd_obj')
        schd.command_queue.put(("take_checkpoints", (items,), {}))
        return TakeCheckpoint(command_queued=True)

class XTrigger(graphene.Mutation):
    class Meta:
        description = """Server-side external event trigger interface."""
    class Arguments:
        event_message = graphene.String(required=True)
        event_id = graphene.String(required=True)
    event_queued = graphene.Boolean()
    def mutate(self, info, event_message, event_id):
        schd = info.context.get('schd_obj')
        schd.ext_trigger_queue.put((event_message, event_id))
        return XTrigger(event_queued=True)

## Mutation declarations
class Mutation(graphene.ObjectType):
    broadcast = Broadcast.Field(
        description=Broadcast._meta.description)
    x_trigger = XTrigger.Field(
        description=XTrigger._meta.description)
    hold_suite = HoldSuite.Field(
        description=HoldSuite._meta.description)
    nudge_suite = NudgeSuite.Field(
        description=NudgeSuite._meta.description)
    put_messages = PutMessages.Field(
        description=PutMessages._meta.description)
    release_suite = ReleaseSuite.Field(
        description=ReleaseSuite._meta.description)
    reload_suite = ReloadSuite.Field(
        description=ReloadSuite._meta.description)
    set_verbosity = SetVerbosity.Field(
        description=SetVerbosity._meta.description)
    stop_suite = StopSuite.Field(
        description=StopSuite._meta.description)
    take_checkpoint = TakeCheckpoint.Field(
        description=TakeCheckpoint._meta.description)
    task_actions = TaskActions.Field(
        description=TaskActions._meta.description)


schema = graphene.Schema(query=Query, mutation=Mutation)
