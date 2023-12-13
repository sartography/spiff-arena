import {useService } from 'bpmn-js-properties-panel';
import { TextFieldEntry } from '@bpmn-io/properties-panel';
import {
  getExtensionValue, setExtensionValue
} from '../extensionHelpers';


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
  const { element, commandStack, moddle, name, label, description, businessObject } = props;
  const debounce = useService('debounceInput');

  const getValue = () => {
    return getExtensionValue(businessObject, name)
  }

  const setValue = value => {
    setExtensionValue(element, name, value, moddle, commandStack, businessObject)
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
