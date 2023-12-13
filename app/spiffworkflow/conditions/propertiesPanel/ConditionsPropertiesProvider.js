import { is } from 'bpmn-js/lib/util/ModelUtil';
import {
  TextAreaEntry
} from '@bpmn-io/properties-panel';
import { useService } from 'bpmn-js-properties-panel';

const LOW_PRIORITY = 500;

export default function ConditionsPropertiesProvider(
  propertiesPanel,
  translate,
  moddle,
  commandStack,
  _elementRegistry
) {
  this.getGroups = function getGroupsCallback(element) {
    return function pushGroup(groups) {
      if (is(element, 'bpmn:SequenceFlow')) {
        const { source } = element;
        if (is(source, 'bpmn:ExclusiveGateway') || is(source, 'bpmn:InclusiveGateway')) {
          groups.push(
            createConditionsGroup(element, translate, moddle, commandStack)
          );
        }
      } else if (is(element, 'bpmn:Event')) {
        const eventDefinitions = element.businessObject.eventDefinitions;
        if (eventDefinitions.filter(ev => is(ev, 'bpmn:ConditionalEventDefinition')).length > 0) {
          groups.push(
            createConditionsGroup(element, translate, moddle, commandStack)
          );
        }
      }
      return groups;
    };
  };
  propertiesPanel.registerProvider(LOW_PRIORITY, this);
}

ConditionsPropertiesProvider.$inject = [
  'propertiesPanel',
  'translate',
  'moddle',
  'commandStack',
  'elementRegistry',
];

function createConditionsGroup(element, translate, moddle, commandStack) {
  return {
    id: 'conditions',
    label: translate('Conditions'),
    entries: conditionGroup(
      element,
      moddle,
      'Condition Expression',
      'Expression to Execute',
      commandStack
    ),
  };
}

function conditionGroup(element, moddle, label, description, commandStack) {
  return [
    {
      id: `condition_expression`,
      element,
      component: ConditionExpressionTextField,
      moddle,
      label,
      description,
      commandStack,
    },
  ];
}

function ConditionExpressionTextField(props) {
  const { element } = props;
  const { moddle } = props;
  const { label } = props;

  const debounce = useService('debounceInput');
  const getValue = () => {
    let conditionExpression;
    if (is(element, 'bpmn:SequenceFlow')) {
      conditionExpression = element.businessObject.conditionExpression;
    } else if (is(element, 'bpmn:Event')) {
      const eventDef = element.businessObject.eventDefinitions.find(ev => is(ev, 'bpmn:ConditionalEventDefinition'));
      conditionExpression = eventDef.condition;
    }
    if (conditionExpression) {
      return conditionExpression.body;
    }
    return '';
  };

  const setValue = (value) => {
    let { conditionExpressionModdleElement } = element.businessObject;
    if (!conditionExpressionModdleElement) {
      conditionExpressionModdleElement = moddle.create('bpmn:Expression');
    }
    conditionExpressionModdleElement.body = value;
    if (is(element, 'bpmn:SequenceFlow')) {
      element.businessObject.conditionExpression = conditionExpressionModdleElement;
    } else if (is(element, 'bpmn:Event')) {
      const eventDef = element.businessObject.eventDefinitions.find(ev => is(ev, 'bpmn:ConditionalEventDefinition'));
      eventDef.condition = conditionExpressionModdleElement;
    }
  };

  return TextAreaEntry({
    element,
    id: `the-id`,
    label,
    getValue,
    setValue,
    debounce,
  });
}
