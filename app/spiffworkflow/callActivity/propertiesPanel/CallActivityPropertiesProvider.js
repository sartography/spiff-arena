import { is } from 'bpmn-js/lib/util/ModelUtil';
import { HeaderButton, TextFieldEntry } from '@bpmn-io/properties-panel';
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
      /* Commented out until such time as we can effectively calculate the list of available processes by process id */
      /*
      {
        id: `called_element_launch_button`,
        element,
        component: LaunchEditorButton,
        moddle,
        commandStack,
        translate,
      },
      */
    ],
  };
}

function getCalledElementValue(element) {
  const { calledElement } = element.businessObject;
  if (calledElement) {
    return calledElement;
  }
  return '';
}

function CalledElementTextField(props) {
  const { element } = props;
  const { translate } = props;

  const debounce = useService('debounceInput');
  const getValue = () => {
    return getCalledElementValue(element);
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

function LaunchEditorButton(props) {
  const { element } = props;
  const eventBus = useService('eventBus');
  return HeaderButton({
    id: 'spiffworkflow-open-call-activity-button',
    class: 'spiffworkflow-properties-panel-button',
    onClick: () => {
      const processId = getCalledElementValue(element);
      eventBus.fire('spiff.callactivity.edit', {
        element,
        processId,
      });
    },
    children: 'Launch Editor',
  });
}
