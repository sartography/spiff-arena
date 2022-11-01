from ..specs.UserTask import UserTask
from ..parser.task_spec import UserTaskParser
from ...bpmn.parser.BpmnParser import full_tag

from SpiffWorkflow.dmn.parser.BpmnDmnParser import BpmnDmnParser
from SpiffWorkflow.dmn.specs.BusinessRuleTask import BusinessRuleTask
from SpiffWorkflow.camunda.parser.task_spec import BusinessRuleTaskParser

from SpiffWorkflow.bpmn.specs.events.StartEvent import StartEvent
from SpiffWorkflow.bpmn.specs.events.EndEvent import EndEvent
from SpiffWorkflow.bpmn.specs.events.IntermediateEvent import IntermediateThrowEvent, IntermediateCatchEvent, BoundaryEvent
from .event_parsers import CamundaStartEventParser, CamundaEndEventParser, \
    CamundaIntermediateCatchEventParser, CamundaIntermediateThrowEventParser, CamundaBoundaryEventParser


class CamundaParser(BpmnDmnParser):

    OVERRIDE_PARSER_CLASSES = {
        full_tag('userTask'): (UserTaskParser, UserTask),
        full_tag('startEvent'): (CamundaStartEventParser, StartEvent),
        full_tag('endEvent'): (CamundaEndEventParser, EndEvent),
        full_tag('intermediateCatchEvent'): (CamundaIntermediateCatchEventParser, IntermediateCatchEvent),
        full_tag('intermediateThrowEvent'): (CamundaIntermediateThrowEventParser, IntermediateThrowEvent),
        full_tag('boundaryEvent'): (CamundaBoundaryEventParser, BoundaryEvent),
        full_tag('businessRuleTask'): (BusinessRuleTaskParser, BusinessRuleTask),
    }
