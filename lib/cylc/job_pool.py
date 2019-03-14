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
    TASK_STATUS_READY, TASK_STATUS_SUBMITTED, TASK_STATUS_SUBMIT_FAILED,
    TASK_STATUS_SUBMIT_RETRYING, TASK_STATUS_RUNNING, TASK_STATUS_SUCCEEDED,
    TASK_STATUS_FAILED)
from cylc.wallclock import (
    get_current_time_string, get_unix_time_from_time_string as str2time)
from cylc.network.schema import QLJob

JOB_STATUSES_ALL = [
    TASK_STATUS_READY,
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
        """Insert job into pool."""
        self.pool[job_conf['job_d']] = QLJob(
            id = job_conf['job_d'],
            batch_sys_name = job_conf['batch_system_name'],
            batch_sys_conf = job_conf['batch_system_conf'],
            directives = job_conf['directives'],
            environment = job_conf['environment'],
            env_script = job_conf['env-script'],
            err_script = job_conf['err-script'],
            exit_script = job_conf['exit-script'],
            extra_logs = job_conf['logfiles'],
            execution_time_limit = job_conf['execution_time_limit'],
            host = job_conf['host'],
            init_script = job_conf['init-script'],
            job_log_dir = job_conf['job_log_dir'],
            owner = job_conf['owner'],
            param_env_tmpl = job_conf['param_env_tmpl'],
            param_var = job_conf['param_var'],
            post_script = job_conf['post-script'],
            pre_script = job_conf['pre-script'],
            script = job_conf['script'],
            state = JOB_STATUSES_ALL[0],
            shell = job_conf['shell'],
            work_sub_dir = job_conf['work_d'],
            submit_num = job_conf['submit_num'],
            task_proxy = job_conf['task_id'])

    def remove_job(self, job_d):
        """Remove job from pool."""
        try:
            del self.pool[job_d]
        except KeyError:
            pass

    def remove_task_jobs(self, task_id):
        """removed all jobs associated with a task from the pool."""
        for job_d, job_obj in self.pool.items():
            if job_obj.task_proxy == task_id:
                del self.pool[job_d]

    def set_job_attr(self, job_d, attr_key, attr_val):
        """Set job attribute."""
        setattr(self.pool[job_d], attr_key, attr_val)

    def set_job_state(self, job_d, status):
        """Set job state."""
        if status in JOB_STATUSES_ALL:
            try:
                self.pool[job_d].state = status
            except KeyError:
                pass

    def set_job_time(self, job_d, event_key, time_str=None):
        """Set an event time in job pool object.

        Set values of both event_key + "_time" and event_key + "_time_string".
        """
        setattr(self.pool[job_d], event_key + '_time', time_str)

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
