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

from SpiffWorkflow.task import Task
from SpiffWorkflow.bpmn.workflow import (
    BpmnWorkflow,
    BpmnSubWorkflow,
)
from SpiffWorkflow.bpmn.event import BpmnEvent
from SpiffWorkflow.bpmn.specs.data_spec import (
    DataObject,
    BpmnIoSpecification,
    TaskDataReference,
)
from SpiffWorkflow.bpmn.specs.bpmn_process_spec import BpmnProcessSpec
from SpiffWorkflow.bpmn.specs.defaults import (
    ManualTask,
    NoneTask,
    UserTask,
    ExclusiveGateway,
    InclusiveGateway,
    ParallelGateway,
    EventBasedGateway,
    ScriptTask,
    ServiceTask,
    StandardLoopTask,
    ParallelMultiInstanceTask,
    SequentialMultiInstanceTask,
    SubWorkflowTask,
    CallActivity,
    TransactionSubprocess,
    StartEvent,
    EndEvent,
    IntermediateCatchEvent,
    IntermediateThrowEvent,
    BoundaryEvent,
    SendTask,
    ReceiveTask,
)
from SpiffWorkflow.bpmn.specs.control import (
    BpmnStartTask,
    SimpleBpmnTask,
    BoundaryEventSplit,
    BoundaryEventJoin,
    _EndJoin,
)
from SpiffWorkflow.bpmn.specs.event_definitions.simple import (
    NoneEventDefinition,
    CancelEventDefinition,
    TerminateEventDefinition,
)
from SpiffWorkflow.bpmn.specs.event_definitions.item_aware_event import (
    SignalEventDefinition,
    ErrorEventDefinition,
    EscalationEventDefinition,
)
from SpiffWorkflow.bpmn.specs.event_definitions.timer import (
    TimeDateEventDefinition,
    DurationTimerEventDefinition,
    CycleTimerEventDefinition,
)
from SpiffWorkflow.bpmn.specs.event_definitions.message import MessageEventDefinition
from SpiffWorkflow.bpmn.specs.event_definitions.multiple import MultipleEventDefinition

from .default.workflow import (
    BpmnWorkflowConverter,
    BpmnSubWorkflowConverter,
    TaskConverter,
    BpmnEventConverter,
)
from .helpers.spec import BpmnDataSpecificationConverter, EventDefinitionConverter
from .default.process_spec import BpmnProcessSpecConverter
from .default.task_spec import (
    BpmnTaskSpecConverter,
    ScriptTaskConverter,
    StandardLoopTaskConverter,
    MultiInstanceTaskConverter,
    SubWorkflowConverter,
    BoundaryEventJoinConverter,
    ConditionalGatewayConverter,
    ExclusiveGatewayConverter,
    ParallelGatewayConverter,
    EventConverter,
    BoundaryEventConverter,
    IOSpecificationConverter,
)
from .default.event_definition import (
    TimerEventDefinitionConverter,
    ErrorEscalationEventDefinitionConverter,
    MessageEventDefinitionConverter,
    MultipleEventDefinitionConverter,
)


DEFAULT_CONFIG = {
    BpmnWorkflow: BpmnWorkflowConverter,
    BpmnSubWorkflow: BpmnSubWorkflowConverter,
    Task: TaskConverter,
    BpmnEvent: BpmnEventConverter,
    DataObject: BpmnDataSpecificationConverter,
    TaskDataReference: BpmnDataSpecificationConverter,
    BpmnIoSpecification: IOSpecificationConverter,
    BpmnProcessSpec: BpmnProcessSpecConverter,
    SimpleBpmnTask: BpmnTaskSpecConverter,
    BpmnStartTask: BpmnTaskSpecConverter,
    _EndJoin: BpmnTaskSpecConverter,
    NoneTask: BpmnTaskSpecConverter,
    ManualTask: BpmnTaskSpecConverter,
    UserTask: BpmnTaskSpecConverter,
    ScriptTask: ScriptTaskConverter,
    StandardLoopTask: StandardLoopTaskConverter,
    ParallelMultiInstanceTask: MultiInstanceTaskConverter,
    SequentialMultiInstanceTask: MultiInstanceTaskConverter,
    SubWorkflowTask: SubWorkflowConverter,
    CallActivity: SubWorkflowConverter,
    TransactionSubprocess: SubWorkflowConverter,
    BoundaryEventSplit: BpmnTaskSpecConverter,
    BoundaryEventJoin: BoundaryEventJoinConverter,
    ExclusiveGateway: ExclusiveGatewayConverter,
    InclusiveGateway: ConditionalGatewayConverter,
    ParallelGateway: ParallelGatewayConverter,
    StartEvent: EventConverter,
    EndEvent: EventConverter,
    IntermediateCatchEvent: EventConverter,
    IntermediateThrowEvent: EventConverter,
    BoundaryEvent: BoundaryEventConverter,
    SendTask: EventConverter,
    ReceiveTask: EventConverter,
    EventBasedGateway: EventConverter,
    CancelEventDefinition: EventDefinitionConverter,
    ErrorEventDefinition: ErrorEscalationEventDefinitionConverter,
    EscalationEventDefinition: ErrorEscalationEventDefinitionConverter,
    MessageEventDefinition: MessageEventDefinitionConverter,
    NoneEventDefinition: EventDefinitionConverter,
    SignalEventDefinition: EventDefinitionConverter,
    TerminateEventDefinition: EventDefinitionConverter,
    TimeDateEventDefinition: TimerEventDefinitionConverter,
    DurationTimerEventDefinition: TimerEventDefinitionConverter,
    CycleTimerEventDefinition: TimerEventDefinitionConverter,
    MultipleEventDefinition: MultipleEventDefinitionConverter,
}