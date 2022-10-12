import { is } from 'bpmn-js/lib/util/ModelUtil';
import { TextFieldEntry } from '@bpmn-io/properties-panel';
import { useService } from 'bpmn-js-properties-panel';

const LOW_PRIORITY = 500;

export default function CallActivityPropertiesProvider(
  propertiesPanel,
  translate,
  moddle,
  commandStack,
  _elementRegistry
) {
  this.getGroups = function getGroupsCallback(element) {
    return function pushGroup(groups) {
      if (is(element, 'bpmn:CallActivity')) {
        groups.push(
          createCalledElementGroup(element, translate, moddle, commandStack)
        );
      }
      return groups;
    };
  };
  propertiesPanel.registerProvider(LOW_PRIORITY, this);
}

CallActivityPropertiesProvider.$inject = [
  'propertiesPanel',
  'translate',
  'moddle',
  'commandStack',
  'elementRegistry',
];

function createCalledElementGroup(element, translate, moddle, commandStack) {
  return {
    id: 'called_element',
    label: translate('Called Element'),
    entries: [
      {
        id: `called_element_text_field`,
        element,
        component: CalledElementTextField,
        moddle,
        commandStack,
        translate,
      },
    ],
  };
}

function CalledElementTextField(props) {
  const { element } = props;
  const { translate } = props;

  const debounce = useService('debounceInput');
  const getValue = () => {
    const { calledElement } = element.businessObject;
    if (calledElement) {
      return calledElement;
    }
    return '';
  };

  const setValue = (value) => {
    element.businessObject.calledElement = value;
  };

  return TextFieldEntry({
    element,
    id: 'process_id',
    label: translate('Process ID'),
    getValue,
    setValue,
    debounce,
  });
}
