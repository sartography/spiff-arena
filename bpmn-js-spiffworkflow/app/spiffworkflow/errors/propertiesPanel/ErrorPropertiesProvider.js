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
  'eventType': 'bpmn:Error',
  'eventDefType': 'bpmn:ErrorEventDefinition',
  'referenceType': 'errorRef',
  'idPrefix': 'error',
};

export default function ErrorPropertiesProvider(
  propertiesPanel,
  translate,
  moddle,
  commandStack,
) {

  this.getGroups = function (element) {
    return function (groups) {
      if (is(element, 'bpmn:Process') || is(element, 'bpmn:Collaboration')) {
        const getErrorArray = getArrayForType('bpmn:Error', 'errorRef', 'Error');
        const errorGroup = getListGroupForType('errors', 'Errors', getErrorArray);
        groups.push(errorGroup({ element, translate, moddle, commandStack }));
      } else if (hasEventType(element, 'bpmn:ErrorEventDefinition')) {
        const getErrorSelector = getSelectorForType(eventDetails);
        const errorGroup = getConfigureGroupForType(eventDetails, 'Error', true, getErrorSelector);
        const group = errorGroup({ element, translate, moddle, commandStack });
        replaceGroup('error', groups, group);
      }
      return groups;
    };
  };
  propertiesPanel.registerProvider(LOW_PRIORITY, this);
}

ErrorPropertiesProvider.$inject = [
  'propertiesPanel',
  'translate',
  'moddle',
  'commandStack',
];
