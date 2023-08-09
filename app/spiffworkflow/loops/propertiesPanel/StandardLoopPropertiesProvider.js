import { is } from 'bpmn-js/lib/util/ModelUtil';
import { useService } from 'bpmn-js-properties-panel';
import {
  Group,
  TextFieldEntry,
  isTextFieldEntryEdited,
  CheckboxEntry,
  isCheckboxEntryEdited,
} from '@bpmn-io/properties-panel';

import { getLoopProperty, setLoopProperty } from './LoopProperty';

const LOW_PRIORITY = 500;

export default function StandardLoopPropertiesProvider(propertiesPanel) {
  this.getGroups = function getGroupsCallback(element) {
    return function pushGroup(groups) {
      if (
        (is(element, 'bpmn:Task') || is(element, 'bpmn:CallActivity') || is(element, 'bpmn:SubProcess')) && 
        typeof(element.businessObject.loopCharacteristics) !== 'undefined' &&
        element.businessObject.loopCharacteristics.$type === 'bpmn:StandardLoopCharacteristics'
      ) {
        const group = {
          id: 'standardLoopCharacteristics',
          component: Group,
          label: 'Standard Loop',
          entries: StandardLoopProps(element),
          shouldOpen: true,
        };
        if (groups.length < 3)
          groups.push(group);
        else
          groups.splice(2, 0, group);
      }
      return groups;
    };
  };
  propertiesPanel.registerProvider(LOW_PRIORITY, this);
}

StandardLoopPropertiesProvider.$inject = ['propertiesPanel'];

function StandardLoopProps(props) {
  const { element } = props;
  return [{
    id: 'loopMaximum',
    component: LoopMaximum,
    isEdited: isTextFieldEntryEdited
  }, {
    id: 'loopCondition',
    component: LoopCondition,
    isEdited: isTextFieldEntryEdited
  }, {
    id: 'testBefore',
    component: TestBefore,
    isEdited: isCheckboxEntryEdited
  }];
}

function LoopMaximum(props) {
  const { element } = props;
  const debounce = useService('debounceInput');
  const translate = useService('translate');
  const commandStack = useService('commandStack');
  const bpmnFactory = useService('bpmnFactory');

  const getValue = () => {
    return getLoopProperty(element, 'loopMaximum');
  };

  const setValue = value => {
    setLoopProperty(element, 'loopMaximum', value, commandStack);
  };

  return TextFieldEntry({
    element,
    id: 'loopMaximum',
    label: translate('Loop Maximum'),
    getValue,
    setValue,
    debounce
  });
}

function TestBefore(props) {
  const { element } = props;
  const debounce = useService('debounceInput');
  const translate = useService('translate');
  const commandStack = useService('commandStack');
  const bpmnFactory = useService('bpmnFactory');

  const getValue = () => {
    return getLoopProperty(element, 'testBefore');
  };

  const setValue = value => {
    setLoopProperty(element, 'testBefore', value, commandStack);
  };

  return CheckboxEntry({
    element,
    id: 'testBefore',
    label: translate('Test Before'),
    getValue,
    setValue,
  });
}

function LoopCondition(props) {
  const { element } = props;
  const debounce = useService('debounceInput');
  const translate = useService('translate');
  const commandStack = useService('commandStack');
  const bpmnFactory = useService('bpmnFactory');

  const getValue = () => {
    return getLoopProperty(element, 'loopCondition');
  };

  const setValue = value => {
    const loopCondition = bpmnFactory.create('bpmn:FormalExpression', {body: value})
    setLoopProperty(element, 'loopCondition', loopCondition, commandStack);
  };

  return TextFieldEntry({
    element,
    id: 'loopCondition',
    label: translate('Loop Condition'),
    getValue,
    setValue,
    debounce
  });
}
