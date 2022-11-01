import { useService } from 'bpmn-js-properties-panel';
import {
  HeaderButton,
  isTextFieldEntryEdited,
  TextAreaEntry,
} from '@bpmn-io/properties-panel';

const SPIFF_PROP = 'spiffworkflow:instructionsForEndUser';

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
function SpiffExtensionInstructionsForEndUser(props) {
  const { element, commandStack, moddle, label, description } = props;
  const debounce = useService('debounceInput');

  const getValue = () => {
    return getPropertyValue(element);
  };

  const setValue = (value) => {
    setProperty(commandStack, moddle, element, value);
  };

  return TextAreaEntry({
    id: 'extension_instruction_for_end_user',
    element,
    description,
    label,
    getValue,
    setValue,
    debounce,
  });
}

function getPropertyObject(element) {
  const bizObj = element.businessObject;
  if (!bizObj.extensionElements) {
    return null;
  }
  return bizObj.extensionElements.get('values').filter(function (e) {
    return e.$instanceOf(SPIFF_PROP);
  })[0];
}

function getPropertyValue(element) {
  const property = getPropertyObject(element);
  if (property) {
    return property.instructionsForEndUser;
  }
  return '';
}

function setProperty(commandStack, moddle, element, value) {
  let property = getPropertyObject(element);
  const { businessObject } = element;
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
      extensionElements: extensions,
    },
  });
}

function LaunchMarkdownEditorButton(props) {
  const { element, moddle, commandStack } = props;
  const eventBus = useService('eventBus');
  return HeaderButton({
    className: 'spiffworkflow-properties-panel-button',
    onClick: () => {
      const markdown = getPropertyValue(element);
      eventBus.fire('markdown.editor.launch', {
        element,
        markdown,
        eventBus,
      });
      // Listen for a response, to update the script.
      eventBus.once('markdown.editor.update', (event) => {
        console.log("Markdown update!!!")
        setProperty(commandStack, moddle, event.element, event.markdown);
      });
    },
    children: 'Launch Editor',
  });
}

/**
 * Generates a text box and button for editing markdown.
 * @param element The element that should get the markdown.
 * @param moddle For updating the underlying xml document when needed.
 * @returns {[{component: (function(*)), isEdited: *, id: string, element},{component: (function(*)), isEdited: *, id: string, element}]}
 */
export default function getEntries(props) {
  const { element, moddle, label, description, translate, commandStack } =
    props;

  return [
    {
      id: `edit_markdown`,
      element,
      component: SpiffExtensionInstructionsForEndUser,
      isEdited: isTextFieldEntryEdited,
      moddle,
      commandStack,
      label,
      description,
    },
    {
      id: `launchMarkdownEditor`,
      element,
      component: LaunchMarkdownEditorButton,
      isEdited: isTextFieldEntryEdited,
      moddle,
      commandStack,
    },
  ];
}
