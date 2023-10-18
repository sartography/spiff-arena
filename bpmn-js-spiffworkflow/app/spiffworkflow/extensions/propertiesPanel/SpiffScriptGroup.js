import {
  HeaderButton,
  TextAreaEntry,
  isTextFieldEntryEdited,
  ListGroup,
} from '@bpmn-io/properties-panel';
import { useService } from 'bpmn-js-properties-panel';
import { ScriptUnitTestArray } from './ScriptUnitTestArray';

export const SCRIPT_TYPE = {
  bpmn: 'bpmn:script',
  pre: 'spiffworkflow:PreScript',
  post: 'spiffworkflow:PostScript',
};

function PythonScript(props) {
  const { element, id } = props;
  const { type } = props;
  const { moddle, commandStack } = props;
  const { label } = props;
  const { description } = props;

  const translate = useService('translate');
  const debounce = useService('debounceInput');

  const getValue = () => {
    return getScriptString(element, type);
  };

  const setValue = (value) => {
    updateScript(commandStack, moddle, element, type, value);
  };

  return TextAreaEntry({
    id,
    element,
    description: translate(description),
    label: translate(label),
    getValue,
    setValue,
    debounce,
  });
}

function LaunchEditorButton(props) {
  const { element, type, moddle, commandStack } = props;
  const eventBus = useService('eventBus');
  return HeaderButton({
    className: 'spiffworkflow-properties-panel-button',
    onClick: () => {
      const script = getScriptString(element, type);
      eventBus.fire('spiff.script.edit', {
        element,
        scriptType: type,
        script,
        eventBus,
      });
      // Listen for a response, to update the script.
      eventBus.once('spiff.script.update', (event) => {
        updateScript(
          commandStack,
          moddle,
          element,
          event.scriptType,
          event.script
        );
      });
    },
    children: 'Launch Editor',
  });
}

/**
 * Finds the value of the given type within the extensionElements
 * given a type of "spiff:preScript", would find it in this, and return
 * the object.
 *
 *  <bpmn:
 <bpmn:userTask id="123" name="My User Task!">
 <bpmn:extensionElements>
 <spiff:preScript>
 me = "100% awesome"
 </spiff:preScript>
 </bpmn:extensionElements>
 ...
 </bpmn:userTask>
 *
 * @returns {string|null|*}
 */
function getScriptObject(element, scriptType) {
  const bizObj = element.businessObject;
  if (scriptType === SCRIPT_TYPE.bpmn) {
    return bizObj;
  }
  if (!bizObj.extensionElements) {
    return null;
  }
  return bizObj.extensionElements
    .get('values')
    .filter(function getInstanceOfType(e) {
      return e.$instanceOf(scriptType);
    })[0];
}

function updateScript(commandStack, moddle, element, scriptType, newValue) {
  const { businessObject } = element;
  let scriptObj = getScriptObject(element, scriptType);
  // Create the script object if needed.
  if (!scriptObj) {
    scriptObj = moddle.create(scriptType);
    if (scriptType !== SCRIPT_TYPE.bpmn) {
      let { extensionElements } = businessObject;
      if (!extensionElements) {
        extensionElements = moddle.create('bpmn:ExtensionElements');
      }
      scriptObj.value = newValue;
      extensionElements.get('values').push(scriptObj);
      commandStack.execute('element.updateModdleProperties', {
        element,
        moddleElement: businessObject,
        properties: {
          extensionElements,
        },
      });
    }
  } else {
    let newProps = { value: newValue };
    if (scriptType === SCRIPT_TYPE.bpmn) {
      newProps = { script: newValue };
    }
    commandStack.execute('element.updateModdleProperties', {
      element,
      moddleElement: scriptObj,
      properties: newProps,
    });
  }
}

function getScriptString(element, scriptType) {
  const scriptObj = getScriptObject(element, scriptType);
  if (scriptObj && scriptObj.value) {
    return scriptObj.value;
  }
  if (scriptObj && scriptObj.script) {
    return scriptObj.script;
  }
  return '';
}

/**
 * Generates a text box and button for editing a script.
 * @param element The elemment that should get the script task.
 * @param scriptType The type of script -- can be a preScript, postScript or a BPMN:Script for script tags
 * @param moddle For updating the underlying xml document when needed.
 * @returns {[{component: (function(*)), isEdited: *, id: string, element},{component: (function(*)), isEdited: *, id: string, element}]}
 */
export default function getEntries(props) {
  const {
    element,
    moddle,
    scriptType,
    label,
    description,
    translate,
    commandStack,
  } = props;

  const entries = [
    {
      id: `pythonScript_${scriptType}`,
      element,
      type: scriptType,
      component: PythonScript,
      isEdited: isTextFieldEntryEdited,
      moddle,
      commandStack,
      label,
      description,
    },
    {
      id: `launchEditorButton${scriptType}`,
      type: scriptType,
      element,
      component: LaunchEditorButton,
      isEdited: isTextFieldEntryEdited,
      moddle,
      commandStack,
    },
  ];

  // do not support testing pre and post scripts at the moment
  if (scriptType === SCRIPT_TYPE.bpmn) {
    entries.push({
      id: `scriptUnitTests${scriptType}`,
      label: translate('Unit Tests'),
      component: ListGroup,
      ...ScriptUnitTestArray({
        element,
        moddle,
        translate,
        commandStack,
      }),
    });
  }

  return entries;
}
