# Copyright (C) 2023 Sartography
#
# This file is part of SpiffWorkflow.
#
# SpiffWorkflow is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3.0 of the License, or (at your option) any later version.
#
# SpiffWorkflow is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301  USA

from copy import deepcopy

from .version_1_1 import move_subprocesses_to_top
from .version_1_2 import (
    convert_timer_expressions,
    add_default_condition_to_cond_task_specs,
    create_data_objects_and_io_specs,
    check_multiinstance,
    remove_loop_reset,
    update_task_states,
    convert_simple_tasks,
    update_bpmn_attributes,
)

def from_version_1_1(old):
    """
    Upgrade v1.1 serialization to v1.2.

    Expressions in timer event definitions have been converted from python expressions to 
    ISO 8601 expressions.

    Cycle timers no longer connect back to themselves.  New children are created from a single
    tasks rather than reusing previously executed tasks.

    All conditions (including the default) are included in the conditions for gateways.

    Data inputs and outputs on process specs were moved inside a BPMNIOSpecification, and
    are now TaskDataReferences; BpmnDataSpecifications that referred to Data Objects are
    now DataObjects.

    Multiinstance tasks were completely refactored, in a way that is simply too difficult to
    migrate.

    Loop reset tasks were removed.
    """
    new = deepcopy(old)
    convert_timer_expressions(new)
    add_default_condition_to_cond_task_specs(new)
    create_data_objects_and_io_specs(new)
    check_multiinstance(new)
    remove_loop_reset(new)
    update_task_states(new)
    convert_simple_tasks(new)
    update_bpmn_attributes(new)
    new['VERSION'] = "1.2"
    return new

def from_version_1_0(old):
    """
    Upgrade v1.0 serializations to v1.1.

    Starting with Spiff 1.1.8, subworkflows are no longer integrated in main task tree.  When
    a subworkflow (a subprocess, transaction, or call activity) is reached, a subprocss is
    added to the top level workflow and the task enters a waiting state until the workflow
    completes.

    To make the serialization backwards compatible, we delete the tasks from the main workflow
    task list and add them to the appropriate subprocess and recreate the remaining subprocess
    attributes based on the task states.
    """
    new = deepcopy(old)
    new['VERSION'] = "1.1"
    move_subprocesses_to_top(new)
    return from_version_1_1(new)

MIGRATIONS = {
    '1.0': from_version_1_0,
    '1.1': from_version_1_1,
}
