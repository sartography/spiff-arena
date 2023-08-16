import { useService } from 'bpmn-js-properties-panel';
import { SelectEntry } from '@bpmn-io/properties-panel';
import {
  findMessageModdleElements,
  getMessageRefElement,
  isMessageEvent,
} from '../MessageHelpers';

/**
 * Allows the selection, or creation, of Message at the Definitions level of a BPMN document.
 */
export function MessageSelect(props) {
  const shapeElement = props.element;
  const { commandStack } = props;
  const debounce = useService('debounceInput');

  const getValue = () => {
    const messageRefElement = getMessageRefElement(shapeElement);
    if (messageRefElement) {
      return messageRefElement.id;
    }
    return '';
  };

  const setValue = (value) => {
    /* Need to add the selected message as the messageRef on the current message task */
    const { businessObject } = shapeElement;
    const messages = findMessageModdleElements(shapeElement.businessObject);
    for (const message of messages) {
      if (message.id === value) {
        if (isMessageEvent(shapeElement)) {
          const messageEventDefinition = businessObject.eventDefinitions[0];
          messageEventDefinition.messageRef = message;
          // call this to update the other elements in the props panel like payload
          commandStack.execute('element.updateModdleProperties', {
            element: shapeElement,
            moddleElement: businessObject,
            properties: {
              messageRef: message,
            },
          });
        } else if (
          businessObject.$type === 'bpmn:ReceiveTask' ||
          businessObject.$type === 'bpmn:SendTask'
        ) {
          commandStack.execute('element.updateModdleProperties', {
            element: shapeElement,
            moddleElement: businessObject,
            properties: {
              messageRef: message,
            },
          });
          commandStack.execute('element.updateProperties', {
            element: shapeElement,
            moddleElement: businessObject,
            properties: {
              messageRef: message,
            },
          });
        }
      }
    }
  };

  const getOptions = (_value) => {
    const messages = findMessageModdleElements(shapeElement.businessObject);
    const options = [];
    for (const message of messages) {
      options.push({ label: message.name, value: message.id });
    }
    return options;
  };

  return (
    <SelectEntry
      id="selectMessage"
      element={shapeElement}
      description="Select the Message to associate with this task or event."
      label="Which message is this associated with?"
      getValue={getValue}
      setValue={setValue}
      getOptions={getOptions}
      debounce={debounce}
    />
  );
}
