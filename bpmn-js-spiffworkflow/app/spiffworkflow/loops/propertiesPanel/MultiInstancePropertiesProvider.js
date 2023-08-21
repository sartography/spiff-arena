import { is } from 'bpmn-js/lib/util/ModelUtil';
import { useService } from 'bpmn-js-properties-panel';
import { TextFieldEntry, isTextFieldEntryEdited } from '@bpmn-io/properties-panel';
import { getLoopProperty, setLoopProperty } from './LoopProperty';

const LOW_PRIORITY = 500;

export default function MultiInstancePropertiesProvider(propertiesPanel) {
  this.getGroups = function getGroupsCallback(element) {
    return function pushGroup(groups) {
      if (is(element, 'bpmn:Task') || is(element, 'bpmn:CallActivity') || is(element, 'bpmn:SubProcess')) {
        let group = groups.filter(g => g.id == 'multiInstance');
        if (group.length == 1)
          updateMultiInstanceGroup(element, group[0]);
      }
      return groups;
    };
  };
  propertiesPanel.registerProvider(LOW_PRIORITY, this);
}

MultiInstancePropertiesProvider.$inject = ['propertiesPanel'];

function updateMultiInstanceGroup(element, group) {
  group.entries = MultiInstanceProps({element});
  group.shouldOpen = true;
}

function MultiInstanceProps(props) {
  const { element } = props;

  const entries = [{
    id: 'loopCardinality',
    component: LoopCardinality,
    isEdited: isTextFieldEntryEdited
  }, {
    id: 'loopDataInputRef',
    component: InputCollection,
    isEdited: isTextFieldEntryEdited
  }, {
    id: 'dataInputItem',
    component: InputItem,
    isEdited: isTextFieldEntryEdited
  }, {
    id: 'loopDataOutputRef',
    component: OutputCollection,
    isEdited: isTextFieldEntryEdited
  }, {
    id: 'dataOutputItem',
    component: OutputItem,
    isEdited: isTextFieldEntryEdited
  }, {
    id: 'completionCondition',
    component: CompletionCondition,
    isEdited: isTextFieldEntryEdited
  }];
  return entries;
}

function LoopCardinality(props) {
  const { element } = props;
  const debounce = useService('debounceInput');
  const translate = useService('translate');
  const commandStack = useService('commandStack');
  const bpmnFactory = useService('bpmnFactory');

  const getValue = () => {
    return getLoopProperty(element, 'loopCardinality');
  };

  const setValue = value => {
    const loopCardinality = bpmnFactory.create('bpmn:FormalExpression', {body: value})
    setLoopProperty(element, 'loopCardinality', loopCardinality, commandStack);
  };

  return TextFieldEntry({
    element,
    id: 'loopCardinality',
    label: translate('Loop Cardinality'),
    getValue,
    setValue,
    debounce,
    description: 'Explicitly set the number of instances'
  });
}

function InputCollection(props) {
  const { element } = props;
  const debounce = useService('debounceInput');
  const translate = useService('translate');
  const commandStack = useService('commandStack');
  const bpmnFactory = useService('bpmnFactory');

  const getValue = () => {
    return getLoopProperty(element, 'loopDataInputRef');
  };

  const setValue = value => {
    const collection = bpmnFactory.create('bpmn:ItemAwareElement', {id: value});
    setLoopProperty(element, 'loopDataInputRef', collection, commandStack);
  };

  return TextFieldEntry({
    element,
    id: 'loopDataInputRef',
    label: translate('Input Collection'),
    getValue,
    setValue,
    debounce,
    description: 'Create an instance for each item in this collection'
  });
}

function InputItem(props) {
  const { element } = props;
  const debounce = useService('debounceInput');
  const translate = useService('translate');
  const commandStack = useService('commandStack');
  const bpmnFactory = useService('bpmnFactory');

  const getValue = () => {
    return getLoopProperty(element, 'inputDataItem');
  };

  const setValue = value => {
    const item = (typeof(value) !== 'undefined') ? bpmnFactory.create('bpmn:DataInput', {id: value, name: value}) : undefined;
    setLoopProperty(element, 'inputDataItem', item, commandStack);
  };

  return TextFieldEntry({
    element,
    id: 'inputDataItem',
    label: translate('Input Element'),
    getValue,
    setValue,
    debounce,
    description: 'Each item in the collection will be copied to this variable'
  });
}

function OutputCollection(props) {
  const { element } = props;
  const debounce = useService('debounceInput');
  const translate = useService('translate');
  const commandStack = useService('commandStack');
  const bpmnFactory = useService('bpmnFactory');

  const getValue = () => {
    return getLoopProperty(element, 'loopDataOutputRef');
  };

  const setValue = value => {
    const collection = bpmnFactory.create('bpmn:ItemAwareElement', {id: value});
    setLoopProperty(element, 'loopDataOutputRef', collection, commandStack);
  };

  return TextFieldEntry({
    element,
    id: 'loopDataOutputRef',
    label: translate('Output Collection'),
    getValue,
    setValue,
    debounce,
    description: 'Create or update this collection with the instance results'
  });
}

function OutputItem(props) {
  const { element } = props;
  const debounce = useService('debounceInput');
  const translate = useService('translate');
  const commandStack = useService('commandStack');
  const bpmnFactory = useService('bpmnFactory');

  const getValue = () => {
    return getLoopProperty(element, 'outputDataItem');
  };

  const setValue = value => {
    const item = (typeof(value) !== 'undefined') ? bpmnFactory.create('bpmn:DataOutput', {id: value, name: value}) : undefined;
    setLoopProperty(element, 'outputDataItem', item, commandStack);
  };

  return TextFieldEntry({
    element,
    id: 'outputDataItem',
    label: translate('Output Element'),
    getValue,
    setValue,
    debounce,
    description: 'The value of this variable will be added to the output collection'
  });
}

function CompletionCondition(props) {
  const { element } = props;
  const debounce = useService('debounceInput');
  const translate = useService('translate');
  const commandStack = useService('commandStack');
  const bpmnFactory = useService('bpmnFactory');

  const getValue = () => {
    return getLoopProperty(element, 'completionCondition');
  };

  const setValue = value => {
    const completionCondition = bpmnFactory.create('bpmn:FormalExpression', {body: value})
    setLoopProperty(element, 'completionCondition', completionCondition, commandStack);
  };

  return TextFieldEntry({
    element,
    id: 'completionCondition',
    label: translate('Completion Condition'),
    getValue,
    setValue,
    debounce,
    description: 'Stop executing this task when this condition is met'
  });
}

