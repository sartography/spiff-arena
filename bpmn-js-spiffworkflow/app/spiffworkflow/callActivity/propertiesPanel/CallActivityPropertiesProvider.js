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
      {
        id: `called_element_launch_button`,
        element,
        component: LaunchEditorButton,
        moddle,
        commandStack,
        translate,
      },
      {
        id: `called_element_find_button`,
        element,
        component: FindProcessButton,
        moddle,
        commandStack,
        translate,
      },
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

function FindProcessButton(props) {
  const { element, commandStack } = props;
  const eventBus = useService('eventBus');
  return HeaderButton({
    id: 'spiffworkflow-search-call-activity-button',
    class: 'spiffworkflow-properties-panel-button',
    onClick: () => {
      const processId = getCalledElementValue(element);

      // First, set up the listen, then fire the event, just
      // in case we are testing and things are happening superfast.
      eventBus.once('spiff.callactivity.update', (response) => {
        commandStack.execute('element.updateProperties', {
          element: response.element,
          moddleElement: response.element.businessObject,
          properties: {
            calledElement: response.value,
          },
        });
      });
      eventBus.fire('spiff.callactivity.search', {
        processId,
        eventBus,
        element
      });
    },
    children: 'Search',
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
