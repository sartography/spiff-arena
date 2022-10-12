import { useService } from 'bpmn-js-properties-panel';
import { TextFieldEntry } from '@bpmn-io/properties-panel';

const SPIFF_PROP = 'spiffworkflow:calledDecisionId';

/**
 * A generic properties' editor for text input.
 * Allows you to provide additional SpiffWorkflow extension properties.  Just
 * uses whatever name is provide on the property, and adds or updates it as
 * needed.
 *
 *
    <bpmn:businessRuleTask id="Activity_0t218za">
      <bpmn:extensionElements>
        <spiffworkflow:calledDecisionId>my_id</spiffworkflow:calledDecisionId>
      </bpmn:extensionElements>
    </bpmn:businessRuleTask>
 *
 * @returns {string|null|*}
 */
export function SpiffExtensionCalledDecision(props) {
  const { element } = props;
  const { commandStack } = props;
  const { moddle } = props;
  const { label } = props;
  const { description } = props;
  const debounce = useService('debounceInput');

  const getPropertyObject = () => {
    const bizObj = element.businessObject;
    if (!bizObj.extensionElements) {
      return null;
    }
    return bizObj.extensionElements.get('values').filter(function (e) {
      return e.$instanceOf(SPIFF_PROP);
    })[0];
  };

  const getValue = () => {
    const property = getPropertyObject();
    if (property) {
      return property.calledDecisionId;
    }
    return '';
  };

  const setValue = (value) => {
    let property = getPropertyObject();
    const { businessObject } = element;
    let extensions = businessObject.extensionElements;

    if (!property) {
      property = moddle.create(SPIFF_PROP);
      if (!extensions) {
        extensions = moddle.create('bpmn:ExtensionElements');
      }
      extensions.get('values').push(property);
    }
    property.calledDecisionId = value;

    commandStack.execute('element.updateModdleProperties', {
      element,
      moddleElement: businessObject,
      properties: {
        extensionElements: extensions,
      },
    });
  };

  return (
    <TextFieldEntry
      id="extension_called_decision"
      element={element}
      description={description}
      label={label}
      getValue={getValue}
      setValue={setValue}
      debounce={debounce}
    />
  );
}
