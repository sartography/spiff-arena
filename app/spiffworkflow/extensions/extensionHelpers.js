const SPIFF_PARENT_PROP = 'spiffworkflow:Properties';
const SPIFF_PROP = 'spiffworkflow:Property';
const PREFIX = 'spiffworkflow:';

/**
 *
 * Spiff Extensions can show up in two distinct ways. The useProperties toggles between them
 *
 * 1. They might be a top level extension, such as a buisness rule, for example:
 *
 *    <bpmn:extensionElements>
 *      <spiffworkflow:calledDecisionId>my_id</spiffworkflow:calledDecisionId>
 *    </bpmn:extensionElements>
 *
 * 2. Or the extension value may exist in a name/value pair inside a Spiffworkflow Properties extension. You would
 * do this if you wanted to hide the values from the SpiffWorkflow enginge completely, and pass these values
 * through unaltered to your actual application.  For Example:
 *
 *    <bpmn:extensionElements>
 *        <spiffworkflow:properties>
 *            <spiffworkflow:property name="formJsonSchemaFilename" value="json_schema.json" />
 *        </spiffworkflow:properties>
 *    </bpmn:extensionElements>
 *
 *
 */


/**
 * Returns the string value of the spiff extension with the given name on the provided element. ""
 * @param useProperties if set to true, will look inside extensions/spiffworkflow:properties  otherwise, just
 * looks for a spiffworkflow:[name] and returns that value inside of it.
 * @param element
 * @param name
 */
export function getExtensionValue(businessObject, name) {

  const useProperties = !name.startsWith(PREFIX);
  let extension;
  if (useProperties) {
    extension = getExtensionProperty(businessObject, name);
  } else {
    extension = getExtension(businessObject, name);
  }
  if (extension) {
    return extension.value;
  }
  return '';
}

export function setExtensionValue(element, name, value, moddle, commandStack, businessObject) {

  const useProperties = !name.startsWith(PREFIX)

  let businessObjectToUse = businessObject
  if (!businessObjectToUse) {
    businessObjectToUse = element.businessObject;
  }

  // Assure we have extensions
  let extensions = businessObjectToUse.extensionElements;
  if (!extensions) {
    extensions = moddle.create('bpmn:ExtensionElements');
  }

  if (useProperties) {
    let properties = getExtension(businessObjectToUse, SPIFF_PARENT_PROP);
    let property = getExtensionProperty(businessObjectToUse, name);
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
  } else {
    let extension = getExtension(businessObjectToUse, name);
    if (!extension) {
      extension = moddle.create(name);
      extensions.get('values').push(extension)
    }
    extension.value = value;
  }

  commandStack.execute('element.updateModdleProperties', {
    element,
    moddleElement: businessObjectToUse,
    properties: {
      extensionElements: extensions,
    },
  });
}

function getExtension(businessObject, name) {
  if (!businessObject.extensionElements) {
    return null;
  }
  const extensionElements = businessObject.extensionElements.get('values');
  return extensionElements.filter(function (extensionElement) {
    if (extensionElement.$instanceOf(name)) {
      return true;
    }
  })[0];
}


function getExtensionProperty(businessObject, name) {
  const parentElement = getExtension(businessObject, SPIFF_PARENT_PROP);
  if (parentElement) {
    return parentElement.get('properties').filter(function (propertyElement) {
      return (
        propertyElement.$instanceOf(SPIFF_PROP) && propertyElement.name === name
      );
    })[0];
  }
  return null;
}
