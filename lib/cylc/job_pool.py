#!/usr/bin/env python2

# THIS FILE IS PART OF THE CYLC SUITE ENGINE.
# Copyright (C) 2008-2019 NIWA & British Crown (Met Office) & Contributors.
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
"""Manage the job pool of a suite.


"""

from parsec.OrderedDict import OrderedDict

from cylc import LOG
from cylc.task_id import TaskID
from cylc.task_job_logs import get_task_job_id
from cylc.task_state import (
    TASK_STATUS_SUBMITTED, TASK_STATUS_SUBMIT_FAILED,
    TASK_STATUS_SUBMIT_RETRYING, TASK_STATUS_RUNNING, TASK_STATUS_SUCCEEDED,
    TASK_STATUS_FAILED)
from cylc.wallclock import get_current_time_string
from cylc.network.schema import QLJob

JOB_STATUSES_ALL = [
    TASK_STATUS_SUBMITTED,
    TASK_STATUS_SUBMIT_FAILED,
    TASK_STATUS_SUBMIT_RETRYING,
    TASK_STATUS_RUNNING,
    TASK_STATUS_SUCCEEDED,
    TASK_STATUS_FAILED,
]

class JobPool(object):
    """Job pool of a suite."""

    ERR_PREFIX_JOBID_MATCH = "No matching jobs found: "
    ERR_PREFIX_JOB_NOT_ON_SEQUENCE = "Invalid cycle point for job: "

    def __init__(self):
        self.pool = {}

    def insert_job(self, job_conf):
        self.pool[job_conf['job_d']] = QLJob(
            id = job_conf['job_d'],
            host = job_conf['host'],
            submit_num = job_conf['submit_num'],
            batch_sys_name = job_conf['batch_system_name'],
            execution_time_limit = job_conf['execution_time_limit'],
            logfiles = job_conf['logfiles'],
            task = job_conf['task_id'])

    def remove_job(self, job_id):
        if job_id in self.pool:
            del self.pool[job_id]

    def remove_task_jobs(self, task_id):
        for job_id, job_obj in self.pool.items():
            if job_obj.task == task_id:
                del self.pool[job_id]

    def set_job_state(self, itask, status):
        job_id = get_task_job_id(
            itask.point, itask.tdef.name, itask.submit_num)
        if job_id in self.jobs:
            self.jobs[job_id].state = status

    @staticmethod
    def parse_job_item(item):
        """Parse point/name/submit_num:state
        or name.point.submit_num:state syntax.
        """
        if ":" in item:
            head, state_str = item.rsplit(":", 1)
        else:
            head, state_str = (item, None)
        if head.count("/") > 1:
            point_str, name_str, submit_num  = head.split("/", 2)
        elif "/" in head:
            point_str, name_str  = head.split("/", 1)
            submit_num = None
        elif head.count(".") > 1:
            name_str, point_str, submit_num  = head.split(".", 2)
        elif "." in head:
            name_str, point_str  = head.split(".", 1)
            submit_num = None
        else:
            name_str, point_str, submit_num = (head, None, None)
        return (point_str, name_str, submit_num, state_str)
