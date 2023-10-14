import { useService } from 'bpmn-js-properties-panel';
import { TextFieldEntry } from '@bpmn-io/properties-panel';
import { getMessageElementForShapeElement } from '../MessageHelpers';

/**
 * Allows the creation, or editing of messageVariable at the bpmn:sendTask level of a BPMN document.
 */
export function MessageVariable(props) {
  const shapeElement = props.element;
  const debounce = useService('debounceInput');
  const messageElement = getMessageElementForShapeElement(shapeElement);
  const disabled = !messageElement;

  const getMessageVariableObject = () => {
    if (messageElement) {
      const { extensionElements } = messageElement;
      if (extensionElements) {
        return messageElement.extensionElements
          .get('values')
          .filter(function getInstanceOfType(e) {
            return e.$instanceOf('spiffworkflow:MessageVariable');
          })[0];
      }
    }
    return null;
  };

  const getValue = () => {
    const messageVariableObject = getMessageVariableObject();
    if (messageVariableObject) {
      return messageVariableObject.value;
    }
    return '';
  };

  const setValue = (value) => {
    let messageVariableObject = getMessageVariableObject();
    if (!messageVariableObject) {
      messageVariableObject = messageElement.$model.create(
        'spiffworkflow:MessageVariable'
      );
      if (!messageElement.extensionElements) {
        messageElement.extensionElements = messageElement.$model.create(
          'bpmn:ExtensionElements'
        );
      }
      messageElement.extensionElements
        .get('values')
        .push(messageVariableObject);
    }
    messageVariableObject.value = value;
  };

  return (
    <TextFieldEntry
      id="messageVariable"
      element={shapeElement}
      description="The name of the variable where we should store payload."
      label="Variable Name"
      disabled={disabled}
      getValue={getValue}
      setValue={setValue}
      debounce={debounce}
    />
  );
}
