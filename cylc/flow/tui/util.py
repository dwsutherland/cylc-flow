#!/usr/bin/env python3
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
"""Common utilities for Tui."""

from contextlib import contextmanager
from getpass import getuser
from itertools import zip_longest
import re
from time import time
from typing import Any, Dict, Optional, Set, Tuple

import urwid

from cylc.flow import LOG
from cylc.flow.flow_mgr import stringify_flow_nums
from cylc.flow.id import Tokens
from cylc.flow.task_state import (
    TASK_STATUS_RUNNING
)
from cylc.flow.tui import (
    JOB_COLOURS,
    JOB_ICON,
    TASK_ICONS,
    TASK_MODIFIERS
)
from cylc.flow.util import deserialise_set
from cylc.flow.wallclock import get_unix_time_from_time_string


# the Tui user, note this is always the same as the workflow owner
# (Tui doesn't do multi-user stuff)
ME = getuser()


Node = Dict[str, Any]
NodeStore = Dict[str, Dict[str, Node]]


MODIFIER_ATTR_MAPPING = {
    # text repr: (internal attr, GraphQL attr)
    'held': ('is_held', 'isHeld'),
    'runahead': ('is_runahead', 'isRunahead'),
    'queued': ('is_queued', 'isQueued'),
    'retry scheduled': ('is_retry', 'isRetry'),
    'wallclock': ('is_wallclock', 'isWallclock'),
    'xtriggered': ('is_xtriggered', 'isXtriggered'),
}


@contextmanager
def suppress_logging():
    """Suppress Cylc logging.

    Log goes to stdout/err which can pollute Urwid apps.
    Patching sys.stdout/err is insufficient so we set the level to something
    silly for the duration of this context manager then set it back again
    afterwards.
    """
    orig_level = LOG.level
    LOG.setLevel(99999)
    yield
    LOG.setLevel(orig_level)


def get_task_icon(
    status,
    *,
    is_held=False,
    is_queued=False,
    is_runahead=False,
    is_retry=False,
    is_wallclock=False,
    is_xtriggered=False,
    colour='body',
    start_time=None,
    mean_time=None,
):
    """Return a Unicode string to represent a task.

    Arguments:
        status (str):
            A Cylc task status string.
        is_held (bool):
            True if the task is held.
        is_queued (bool):
            True if the task is queued.
        is_runahead (bool):
            True if the task is runahead limited.
        colour (str):
            Set the icon colour. If not provided, the default foreground text
            colour will be used.
        start_time (str):
            Start date time string.
        mean_time (int):
            Execution mean time.

    Returns:
        list - Text content for the urwid.Text widget,
        may be a string, tuple or list, see urwid docs.

    """
    ret = []
    if is_held:
        ret.append((colour, TASK_MODIFIERS['held']))
    elif is_runahead:
        ret.append((colour, TASK_MODIFIERS['runahead']))
    elif is_queued:
        ret.append((colour, TASK_MODIFIERS['queued']))
    elif is_retry:
        ret.append((colour, TASK_MODIFIERS['retry']))
    elif is_wallclock:
        ret.append((colour, TASK_MODIFIERS['wallclock']))
    elif is_xtriggered:
        ret.append((colour, TASK_MODIFIERS['xtriggered']))
    if (
        status == TASK_STATUS_RUNNING
        and start_time
        and mean_time
    ):
        start_time = get_unix_time_from_time_string(start_time)
        progress = (time() - start_time) / mean_time
        if progress >= 0.75:
            status = f'{TASK_STATUS_RUNNING}:75'
        elif progress >= 0.5:
            status = f'{TASK_STATUS_RUNNING}:50'
        elif progress >= 0.25:
            status = f'{TASK_STATUS_RUNNING}:25'
        else:
            status = f'{TASK_STATUS_RUNNING}:0'
    ret.append((colour, TASK_ICONS[status]))
    return ret


def get_status_str(data):
    """Return a text represenation of a workflow, cycle, family, task or job.

    Args:
        data: A data node from the Tui tree (i.e. `value['data']`).

    """
    attrs = []

    # workflow state info
    if data.get('status'):
        attrs.append(data['status'])

    # task state info
    if data.get('state'):
        state_attrs = [
            modifier_text
            for modifier_text, (_, data_attr) in MODIFIER_ATTR_MAPPING.items()
            if data.get(data_attr, None)
        ]
        _attr = data['state']
        if state_attrs:
            _attr += f' ({", ".join(state_attrs)})'
        attrs.append(_attr)

    # task flow info
    if data.get('flowNums', '[1]') != '[1]':
        attrs.append(f'flows={format_flow_nums(data["flowNums"])}')

    return ', '.join(attrs)


def idpop(id_):
    """Remove the last element of a node id.

    Examples:
        >>> idpop('w//c/t/j')
        'w//c/t'
        >>> idpop('c/t/j')
        '//c/t'
        >>> idpop('c/t')
        '//c'
        >>> idpop('c')
        Traceback (most recent call last):
        ValueError: No tokens provided
        >>> idpop('')
        Traceback (most recent call last):
        ValueError: Invalid Cylc identifier: //

    """
    relative = '//' not in id_
    tokens = Tokens(id_, relative=relative)
    tokens.pop_token()
    return tokens.id


def compute_tree(data: dict, prune_families: bool = False) -> Node:
    """Digest GraphQL data to produce a tree.

    Args:
        data:
            The workflow data as returned from the GraphQL query.
        prune_families:
            If True any empty families will be removed from the tree.
            Turn this on if task state filters are active.

    """
    root_node: Node = add_node('root', 'root', create_node_store(), data={})

    for flow in data['workflows']:
        nodes: NodeStore = create_node_store()  # nodes for this workflow
        flow_node = add_node(
            'workflow', flow['id'], nodes, data=flow)
        root_node['children'].append(flow_node)

        # populate cycle nodes
        for cycle in flow.get('cyclePoints', []):
            cycle['id'] = idpop(cycle['id'])  # strip the family off of the id
            cycle_node = add_node('cycle', cycle['id'], nodes, data=cycle)
            flow_node['children'].append(cycle_node)

        # populate family nodes
        for family in flow.get('familyProxies', []):
            add_node('family', family['id'], nodes, data=family)

        # create cycle/family tree
        for family in flow.get('familyProxies', []):
            family_node = add_node(
                'family', family['id'], nodes)
            first_parent = family['firstParent']
            if (
                first_parent
                and first_parent['name'] != 'root'
            ):
                parent_node = add_node(
                    'family', first_parent['id'], nodes)
                parent_node['children'].append(family_node)
            else:
                add_node(
                    'cycle', idpop(family['id']), nodes
                )['children'].append(family_node)

        # add leaves
        for task in flow.get('taskProxies', []):
            # If there's no first parent, the child will have been deleted
            # during/after API query resolution. So ignore.
            if not task['firstParent']:
                continue
            task_node = add_node(
                'task', task['id'], nodes, data=task)
            if task['firstParent']['name'] == 'root':
                family_node = add_node(
                    'cycle', idpop(task['id']), nodes)
            else:
                family_node = add_node(
                    'family', task['firstParent']['id'], nodes)
            family_node['children'].append(task_node)
            for job in task['jobs']:
                job_node = add_node(
                    'job', job['id'], nodes, data=job)
                job_info_node = add_node(
                    'job_info', job['id'] + '_info', nodes, data=job)
                job_node['children'] = [job_info_node]
                task_node['children'].append(job_node)

        # trim empty families / cycles (cycles are just "root" families)
        if prune_families:
            _prune_empty_families(nodes)

        # sort
        for type_ in ('workflow', 'cycle', 'family', 'job'):
            for node in nodes[type_].values():
                # NOTE: jobs are sorted by submit-num in the GraphQL query
                node['children'].sort(
                    key=lambda x: NaturalSort(x['id_'])
                )

        # spring nodes
        if 'port' not in flow:
            # the "port" field is only available via GraphQL
            # so we are not connected to this workflow yet
            flow_node['children'].append(
                add_node(
                    '#spring',
                    '#spring',
                    nodes,
                    data={
                        'id': flow.get('_tui_data', 'Loading ...'),
                    }
                )
            )

    return root_node


def _prune_empty_families(nodes: NodeStore) -> None:
    """Prune empty families from the tree.

    Note, cycles are "root" families.

    We can end up with empty families when filtering by task state. We filter
    tasks by state in the GraphQL query (so we don't need to perform this
    filtering client-side), however, we cannot filter families by state because
    the family state is an aggregate representing a collection of tasks (and or
    families).

    Args:
        nodes: Dictionary containing all nodes present in the tree.

    """
    # go through all families and cycles
    stack: Set[str] = {*nodes['family'], *nodes['cycle']}
    while stack:
        family_id = stack.pop()

        if family_id in nodes['family']:
            # this is a family
            family = nodes['family'][family_id]
            if len(family['children']) > 0:
                continue

            # this family is empty -> find its parent (family/cycle)
            _first_parent = family['data']['firstParent']
            if _first_parent['name'] == 'root':
                parent_type = 'cycle'
                parent_id = idpop(_first_parent['id'])
            else:
                parent_type = 'family'
                parent_id = _first_parent['id']

        elif family_id in nodes['cycle']:
            # this is a cycle
            family = nodes['cycle'][family_id]
            if len(family['children']) > 0:
                continue

            # this cycle is empty -> find its parent (workflow)
            parent_type = 'workflow'
            parent_id = idpop(family_id)

        else:
            # this node has already been pruned
            continue

        # remove the node from its parent
        nodes[parent_type][parent_id]['children'].remove(family)
        if parent_type in {'family', 'cycle'}:
            # recurse up the family tree
            stack.add(parent_id)


class NaturalSort:
    """An object to use as a sort key for sorting strings as a human would.

    This recognises numerical patterns within strings.

    Examples:
        >>> N = NaturalSort

        String comparisons work as normal:
        >>> N('') < N('')
        False
        >>> N('a') < N('b')
        True
        >>> N('b') < N('a')
        False

        Integer comparisons work as normal:
        >>> N('9') < N('10')
        True
        >>> N('10') < N('9')
        False

        Integers rank higher than strings:
        >>> N('1') < N('a')
        True
        >>> N('a') < N('1')
        False

        Integers within strings are sorted numerically:
        >>> N('a9b') < N('a10b')
        True
        >>> N('a10b') < N('a9b')
        False

        Lexicographical rules apply when substrings match:
        >>> N('a1b2') < N('a1b2c3')
        True
        >>> N('a1b2c3') < N('a1b2')
        False

        Equality works as per regular string rules:
        >>> N('a1b2c3') == N('a1b2c3')
        True

    """

    PATTERN = re.compile(r'(\d+)')

    def __init__(self, value):
        self.value = tuple(
            int(item) if item.isdigit() else item
            for item in self.PATTERN.split(value)
            # remove empty strings if value ends with a digit
            if item
        )

    def __eq__(self, other):
        return self.value == other.value

    def __lt__(self, other):
        for this, that in zip_longest(self.value, other.value):
            if this is None:
                return True
            if that is None:
                return False
            this_isstr = isinstance(this, str)
            that_isstr = isinstance(that, str)
            if this_isstr and that_isstr:
                if this == that:
                    continue
                return this < that
            this_isint = isinstance(this, int)
            that_isint = isinstance(that, int)
            if this_isint and that_isint:
                if this == that:
                    continue
                return this < that
            if this_isint and that_isstr:
                return True
            if this_isstr and that_isint:
                return False
        return False


def dummy_flow(data) -> Node:
    return add_node(
        'workflow',
        data['id'],
        create_node_store(),
        data
    )


def create_node_store() -> NodeStore:
    """Returns a "node store" dictionary for use with add_nodes."""
    return {  # node_type: {node_id: node}
        # the root of the tree
        'root': {},
        # spring nodes load the workflow when visited
        '#spring': {},
        # workflow//cycle/<task/family>/job
        'workflow': {},
        'cycle': {},
        'family': {},
        'task': {},
        'job': {},
        # the node under a job that contains metadata (platform, job_id, etc)
        'job_info': {},
    }


def add_node(
    type_: str,
    id_: str,
    nodes: NodeStore,
    data: Optional[dict] = None,
) -> Node:
    """Create a node add it to the store and return it.

    Arguments:
        type_ (str):
            A string to represent the node type.
        id_ (str):
            A unique identifier for this node.
        nodes (dict):
            The node store to add the new node to.
        data (dict):
            An optional dictionary of data to add to this node.
            Can be left to None if retrieving a node from the store.

    Returns:
        dict - The requested node.

    """
    if id_ not in nodes[type_]:
        nodes[type_][id_] = {
            'children': [],
            'id_': id_,
            'data': data or {},
            'type_': type_
        }
    return nodes[type_][id_]


def get_job_icon(status):
    """Return a unicode string to represent a job.

    Arguments:
        status (str): A Cylc job status string.

    Returns:
        list - Text content for the urwid.Text widget,
        may be a string, tuple or list, see urwid docs.

    """
    return [
        (f'job_{status}', JOB_ICON)
    ]


def get_task_status_summary(flow):
    """Return a task status summary line for this workflow.

    Arguments:
        flow (dict):
            GraphQL JSON response for this workflow.

    Returns:
        list - Text list for the urwid.Text widget.

    """
    state_totals = flow['stateTotals']
    return [
        [
            ' ',
            (f'job_{state}', str(state_totals[state])),
            (f'job_{state}', JOB_ICON)
        ]
        for state, colour in JOB_COLOURS.items()
        if state in state_totals
        if state_totals[state]
    ]


def _render_user(node, data):
    return f'~{ME}'


def _render_job_info(node, data):
    key_len = max(len(key) for key in data)
    ret = [
        f'{key} {" " * (key_len - len(key))} {value}\n'
        for key, value in data.items()
    ]
    ret[-1] = ret[-1][:-1]  # strip trailing newline
    return ret


def _render_job(node, data):
    return [
        f'#{data["submitNum"]:02d} ',
        get_job_icon(data['state'])
    ]


def _render_task(node, data):
    start_time = None
    mean_time = None
    try:
        # due to sorting this is the most recent job
        first_child = node.get_child_node(0)
    except IndexError:
        first_child = None

    # progress information
    if data['state'] == TASK_STATUS_RUNNING and first_child:
        start_time = first_child.get_value()['data']['startedTime']
        mean_time = data['task']['meanElapsedTime']

    if data['flowNums'] == '[]':
        # grey out no-flow tasks
        colour = 'diminished'
    else:
        # default foreground colour for everything else
        colour = 'body'

    # the task icon
    ret = get_task_icon(
        data['state'],
        colour=colour,
        start_time=start_time,
        mean_time=mean_time,
        **{
            modifier_attr: data.get(data_attr, False)
            for _, (modifier_attr, data_attr) in MODIFIER_ATTR_MAPPING.items()
        }
    )

    # the most recent job status
    ret.append(' ')
    if first_child:
        state = first_child.get_value()['data']['state']
        ret += [(f'job_{state}', f'{JOB_ICON}'), ' ']

    # the task name
    ret.append((colour, f'{data["name"]}'))
    return ret


def _render_family(node, data):
    return [
        get_task_icon(
            data['state'],
            **{
                modifier_attr: data.get(data_attr, False)
                for _, (modifier_attr, data_attr)
                in MODIFIER_ATTR_MAPPING.items()
            },
        ),
        ' ',
        Tokens(data['id']).pop_token()[1]
    ]


def _render_unknown(node, data):
    try:
        state_totals = get_task_status_summary(data)
        status = data['status']
        status_msg = [
            (
                'title',
                _display_workflow_id(data),
            ),
            ' - ',
            (
                f'workflow_{status}',
                status
            )
        ]
    except KeyError:
        return Tokens(data['id']).pop_token()[1]

    return [*status_msg, *state_totals]


def _display_workflow_id(data):
    return data['name']


RENDER_FUNCTIONS = {
    'user': _render_user,
    'root': _render_user,
    'job_info': _render_job_info,
    'job': _render_job,
    'task': _render_task,
    'cycle': _render_family,
    'family': _render_family,
}


def render_node(node, data, type_):
    """Render a tree node as text.

    Args:
        node (MonitorNode):
            The node to render.
        data (dict):
            Data associated with that node.
        type_ (str):
            The node type (e.g. `task`, `job`, `family`).

    """
    return RENDER_FUNCTIONS.get(type_, _render_unknown)(node, data)


def extract_context(selection):
    """Return a dictionary of all component types in the selection.

    Args:
        selection (list):
            List of element id's as extracted from the data store / graphql.

    Examples:
        >>> extract_context(['~a/b', '~a/c'])
        {'user': ['a'], 'workflow': ['b', 'c']}

        >>> extract_context(['~a/b//c/d/e']
        ... )  # doctest: +NORMALIZE_WHITESPACE
        {'user': ['a'], 'workflow': ['b'], 'cycle': ['c'],
        'task': ['d'], 'job': ['e']}

        >>> list(extract_context(['root']).keys())
        ['user']

    """
    ret = {}
    for item in selection:
        if item == 'root':
            # special handling for the Tui "root" node
            # (this represents the workflow owner which is always the same as
            # user for Tui)
            ret['user'] = ME
            continue
        tokens = Tokens(item)
        for key, value in tokens.items():
            if (
                value
                and not key.endswith('_sel')  # ignore selectors
            ):
                lst = ret.setdefault(key, [])
                if value not in lst:
                    lst.append(value)
    return ret


def get_text_dimensions(text: str) -> Tuple[int, int]:
    """Return the monospace size of a block of multiline text.

    Examples:
        >>> get_text_dimensions('foo')
        (3, 1)

        >>> get_text_dimensions('''
        ...     foo bar
        ...     baz
        ... ''')
        (11, 3)

        >>> get_text_dimensions('')
        (0, 0)

    """
    lines = text.splitlines()
    return max((0, *(len(line) for line in lines))), len(lines)


class ListBoxPlus(urwid.ListBox):
    """An extended list box that responds to the "home" and "end" keys."""

    def keypress(self, size, key):
        # NOTE: The urwid.ListBox class supports "page up" and "page down" but
        # not "home" and "end". The implementation of these methods is highly
        # non-trivial.
        if key == 'home':
            # press "page up" until we stop moving
            target = self.get_scrollpos(size)
            while True:
                super().keypress(size, 'page up')
                new_target = self.get_scrollpos(size)
                if target == new_target:
                    break
                target = new_target
        elif key == 'end':
            # press "page down" until we stop moving
            target = self.get_scrollpos(size)
            while True:
                super().keypress(size, 'page down')
                new_target = self.get_scrollpos(size)
                if target == new_target:
                    break
                target = new_target
        else:
            return super().keypress(size, key)


def format_flow_nums(serialised_flow_nums: str) -> str:
    """Return a user-facing representation of task serialised flow nums.

    Examples:
        >>> format_flow_nums('[1,2]')
        '1,2'
        >>> format_flow_nums('[]')
        'None'

    """
    return stringify_flow_nums(deserialise_set(serialised_flow_nums)) or 'None'
