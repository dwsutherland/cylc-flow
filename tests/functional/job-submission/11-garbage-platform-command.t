#!/usr/bin/env bash
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
#-------------------------------------------------------------------------------
# Test job submission rundb task_jobs entry with garbage host command.
. "$(dirname "$0")/test_header"

set_test_number 3

create_test_global_config '
[platforms]
    [[badhost]]
'

install_workflow "${TEST_NAME_BASE}" "${TEST_NAME_BASE}"
run_ok "${TEST_NAME_BASE}-validate" cylc validate "${WORKFLOW_NAME}"
workflow_run_ok "${TEST_NAME_BASE}-run" \
    cylc play --debug --no-detach --reference-test "${WORKFLOW_NAME}"

sqlite3 \
    "$RUN_DIR/${WORKFLOW_NAME}/log/db" \
    "SELECT submit_num,submit_status FROM task_jobs WHERE name=='t1'" \
    >'sqlite3.out'
cmp_ok 'sqlite3.out' <<'__OUT__'
1|1
2|0
__OUT__
#-------------------------------------------------------------------------------
purge
exit
