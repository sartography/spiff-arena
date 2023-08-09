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
  'eventType': 'bpmn:Signal',
  'eventDefType': 'bpmn:SignalEventDefinition',
  'referenceType': 'signalRef',
  'idPrefix': 'signal',
};

export default function SignalPropertiesProvider(
  propertiesPanel,
  translate,
  moddle,
  commandStack,
) {

  this.getGroups = function (element) {
    return function (groups) {
      if (is(element, 'bpmn:Process') || is(element, 'bpmn:Collaboration')) {
        const getSignalArray = getArrayForType('bpmn:Signal', 'signalRef', 'Signal');
        const signalGroup = getListGroupForType('signals', 'Signals', getSignalArray);
        groups.push(signalGroup({ element, translate, moddle, commandStack }));
      } else if (hasEventType(element, 'bpmn:SignalEventDefinition')) {
        const getSignalSelector = getSelectorForType(eventDetails);
        const signalGroup = getConfigureGroupForType(eventDetails, 'Signal', false, getSignalSelector);
        const group = signalGroup({ element, translate, moddle, commandStack });
        replaceGroup('signal', groups, group);
      }
      return groups;
    };
  };
  propertiesPanel.registerProvider(LOW_PRIORITY, this);
}

SignalPropertiesProvider.$inject = [
  'propertiesPanel',
  'translate',
  'moddle',
  'commandStack',
];
