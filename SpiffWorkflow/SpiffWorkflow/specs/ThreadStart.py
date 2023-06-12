# Copyright (C) 2007 Samuel Abels
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

from .base import TaskSpec
from SpiffWorkflow.task import TaskState


class ThreadStart(TaskSpec):

    """
    This class implements the task the is placed at the beginning
    of each thread. It is NOT supposed to be used! It is purely internal,
    and used only by the ThreadSplit task.
    The task has no inputs and at least one output.
    If more than one output is connected, the task does an implicit
    parallel split.
    """

    def __init__(self, wf_spec, name='ThreadStart', **kwargs):
        """
        Constructor. The name of this task is *always* 'ThreadStart'.

        :type  wf_spec: WorkflowSpec
        :param wf_spec: A reference to the workflow specification.
        :type  kwargs: dict
        :param kwargs: See :class:`SpiffWorkflow.specs.TaskSpec`.
        """
        TaskSpec.__init__(self, wf_spec, name, **kwargs)
        self.internal = True

    def _run_hook(self, my_task):
        my_task._assign_new_thread_id()
        my_task._sync_children(self.outputs, TaskState.READY)
        return True

    def serialize(self, serializer):
        return serializer.serialize_thread_start(self)

    @classmethod
    def deserialize(self, serializer, wf_spec, s_state):
        return serializer.deserialize_thread_start(wf_spec, s_state)
