import { useService } from 'bpmn-js-properties-panel';
import { TextAreaEntry } from '@bpmn-io/properties-panel';
import { getMessageElementForShapeElement } from '../MessageHelpers';

/**
 * Allows the creation, or editing of messagePayload at the bpmn:sendTask level of a BPMN document.
 */
export function MessagePayload(props) {
  const shapeElement = props.element;
  const debounce = useService('debounceInput');
  const messageElement = getMessageElementForShapeElement(shapeElement);
  const disabled = !messageElement;

  const getMessagePayloadObject = () => {
    if (messageElement) {
      const { extensionElements } = messageElement;
      if (extensionElements) {
        return messageElement.extensionElements
          .get('values')
          .filter(function getInstanceOfType(e) {
            return e.$instanceOf('spiffworkflow:MessagePayload');
          })[0];
      }
    }
    return null;
  };

  const getValue = () => {
    const messagePayloadObject = getMessagePayloadObject();
    if (messagePayloadObject) {
      return messagePayloadObject.value;
    }
    return '';
  };

  const setValue = (value) => {
    let messagePayloadObject = getMessagePayloadObject();
    if (!messagePayloadObject) {
      messagePayloadObject = messageElement.$model.create(
        'spiffworkflow:MessagePayload'
      );
      if (!messageElement.extensionElements) {
        messageElement.extensionElements = messageElement.$model.create(
          'bpmn:ExtensionElements'
        );
      }
      messageElement.extensionElements.get('values').push(messagePayloadObject);
    }
    messagePayloadObject.value = value;
  };

  return (
    <TextAreaEntry
      id="messagePayload"
      element={shapeElement}
      description="The payload of the message."
      label="Payload"
      disabled={disabled}
      getValue={getValue}
      setValue={setValue}
      debounce={debounce}
    />
  );
}
