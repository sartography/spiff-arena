import { is } from 'bpmn-js/lib/util/ModelUtil';
import { getRoot } from '../../helpers';
import { getArrayForType, getListGroupForType } from '../../eventList.js';
import { hasEventType,
  replaceGroup,
  getSelectorForType,
  getConfigureGroupForType
} from '../../eventSelect.js';

const LOW_PRIORITY = 500;

const eventDetails = {
  'eventType': 'bpmn:Escalation',
  'eventDefType': 'bpmn:EscalationEventDefinition',
  'referenceType': 'escalationRef',
  'idPrefix': 'escalation',
};

export default function EscalationPropertiesProvider(
  propertiesPanel,
  translate,
  moddle,
  commandStack,
) {

  this.getGroups = function (element) {
    return function (groups) {
      if (is(element, 'bpmn:Process') || is(element, 'bpmn:Collaboration')) {
        const getEscalationArray = getArrayForType('bpmn:Escalation', 'escalationRef', 'Escalation');
        const escalationGroup = getListGroupForType('escalations', 'Escalations', getEscalationArray);
        groups.push(escalationGroup({ element, translate, moddle, commandStack }));
      } else if (hasEventType(element, 'bpmn:EscalationEventDefinition')) {
        const getEscalationSelector = getSelectorForType(eventDetails);
        const escalationGroup = getConfigureGroupForType(eventDetails, 'Escalation', true, getEscalationSelector);
        const group = escalationGroup({ element, translate, moddle, commandStack });
        replaceGroup('escalation', groups, group);
      }
      return groups;
    };
  };
  propertiesPanel.registerProvider(LOW_PRIORITY, this);
}

EscalationPropertiesProvider.$inject = [
  'propertiesPanel',
  'translate',
  'moddle',
  'commandStack',
];
