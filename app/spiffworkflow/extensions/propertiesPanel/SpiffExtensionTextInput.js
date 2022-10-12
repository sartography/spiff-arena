import {useService } from 'bpmn-js-properties-panel';
import { TextFieldEntry } from '@bpmn-io/properties-panel';

const SPIFF_PARENT_PROP = "spiffworkflow:properties"
const SPIFF_PROP = "spiffworkflow:property"

/**
 * A generic properties' editor for text input.
 * Allows you to provide additional SpiffWorkflow extension properties.  Just
 * uses whatever name is provide on the property, and adds or updates it as
 * needed.
 *
       <bpmn:extensionElements>
           <spiffworkflow:properties>
               <spiffworkflow:property name="formJsonSchemaFilename" value="json_schema.json" />
               <spiffworkflow:property name="formUiSchemaFilename" value="ui_schema.json" />
           </spiffworkflow:properties>
       </bpmn:extensionElements>
 *
 * @returns {string|null|*}
 */
export function SpiffExtensionTextInput(props) {
  const element = props.element;
  const commandStack = props.commandStack, moddle = props.moddle;
  const name = props.name, label = props.label, description = props.description;
  const debounce = useService('debounceInput');

  const getPropertiesObject = () => {
    const bizObj = element.businessObject;
    if (!bizObj.extensionElements) {
      return null;
    } else {
      const extensionElements = bizObj.extensionElements.get("values");
      return extensionElements.filter(function (extensionElement) {
        if (extensionElement.$instanceOf(SPIFF_PARENT_PROP)) {
          return extensionElement;
        }
      })[0];
    }
  }

  const getPropertyObject = () => {
    const parentElement = getPropertiesObject();
    if (parentElement) {
      return parentElement.get("properties").filter(function (propertyElement) {
        return propertyElement.$instanceOf(SPIFF_PROP) && propertyElement.name === name;
      })[0];
    }
    return null;
  }

  const getValue = () => {
    const property = getPropertyObject()
    if (property) {
      return property.value;
    }
    return ""
  }

  const setValue = value => {
    let properties = getPropertiesObject()
    let property = getPropertyObject()
    let businessObject = element.businessObject;
    let extensions = businessObject.extensionElements;

    if (!extensions) {
      extensions = moddle.create('bpmn:ExtensionElements');
    }
    if (!properties) {
      properties = moddle.create(SPIFF_PARENT_PROP);
      extensions.get('values').push(properties);
    }
    if (!property) {
      property = moddle.create(SPIFF_PROP);
      properties.get('properties').push(property);
    }
    property.value = value;
    property.name = name;

    commandStack.execute('element.updateModdleProperties', {
      element,
      moddleElement: businessObject,
      properties: {
        "extensionElements": extensions
      }
    });
  };

  return <TextFieldEntry
    id={'extension_' + name}
    element={element}
    description={description}
    label={label}
    getValue={getValue}
    setValue={setValue}
    debounce={debounce}
  />;

}
