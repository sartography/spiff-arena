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
  pre: 'spiffworkflow:preScript',
  post: 'spiffworkflow:postScript',
};

function PythonScript(props) {
  const { element, id } = props;
  const { type } = props;
  const { moddle } = props;
  const { label } = props;
  const { description } = props;

  const translate = useService('translate');
  const debounce = useService('debounceInput');

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
  const getScriptObject = () => {
    const bizObj = element.businessObject;
    if (type === SCRIPT_TYPE.bpmn) {
      return bizObj;
    }
    if (!bizObj.extensionElements) {
      return null;
    }
    return bizObj.extensionElements
      .get('values')
      .filter(function getInstanceOfType(e) {
        return e.$instanceOf(type);
      })[0];
  };

  const getValue = () => {
    const scriptObj = getScriptObject();
    if (scriptObj) {
      return scriptObj.script;
    }
    return '';
  };

  const setValue = (value) => {
    const { businessObject } = element;
    let scriptObj = getScriptObject();
    // Create the script object if needed.
    if (!scriptObj) {
      scriptObj = moddle.create(type);
      if (type !== SCRIPT_TYPE.bpmn) {
        if (!businessObject.extensionElements) {
          businessObject.extensionElements = moddle.create(
            'bpmn:ExtensionElements'
          );
        }
        businessObject.extensionElements.get('values').push(scriptObj);
      }
    }
    scriptObj.script = value;
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
  const { element, type } = props;
  const eventBus = useService('eventBus');
  // fixme: add a call up date as a property
  return HeaderButton({
    className: 'spiffworkflow-properties-panel-button',
    onClick: () => {
      eventBus.fire('launch.script.editor', { element, type });
    },
    children: 'Launch Editor',
  });
}

/**
 * Generates a python script.
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
