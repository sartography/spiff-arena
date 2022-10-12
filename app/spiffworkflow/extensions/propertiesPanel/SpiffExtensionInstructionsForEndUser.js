import {useService } from 'bpmn-js-properties-panel';
import { TextAreaEntry } from '@bpmn-io/properties-panel';

const SPIFF_PROP = "spiffworkflow:instructionsForEndUser"

/**
 * A generic properties' editor for text input.
 * Allows you to provide additional SpiffWorkflow extension properties.  Just
 * uses whatever name is provide on the property, and adds or updates it as
 * needed.
 *
 *
 *
 * @returns {string|null|*}
 */
export function SpiffExtensionInstructionsForEndUser(props) {
  const element = props.element;
  const commandStack = props.commandStack, moddle = props.moddle;
  const label = props.label, description = props.description;
  const debounce = useService('debounceInput');

  const getPropertyObject = () => {
    const bizObj = element.businessObject;
    if (!bizObj.extensionElements) {
      return null;
    } else {
      return bizObj.extensionElements.get("values").filter(function (e) {
        return e.$instanceOf(SPIFF_PROP)
      })[0];
    }
  }

  const getValue = () => {
    const property = getPropertyObject()
    if (property) {
      return property.instructionsForEndUser;
    }
    return ""
  }

  const setValue = value => {
    let property = getPropertyObject()
    let businessObject = element.businessObject;
    let extensions = businessObject.extensionElements;

    if (!property) {
      property = moddle.create(SPIFF_PROP);
      if (!extensions) {
        extensions = moddle.create('bpmn:ExtensionElements');
      }
      extensions.get('values').push(property);
    }
    property.instructionsForEndUser = value;

    commandStack.execute('element.updateModdleProperties', {
      element,
      moddleElement: businessObject,
      properties: {
        "extensionElements": extensions
      }
    });
  };

  return TextAreaEntry({
    id: 'extension_instruction_for_end_user',
    element: element,
    description: description,
    label: label,
    getValue: getValue,
    setValue: setValue,
    debounce: debounce,
  })
}
