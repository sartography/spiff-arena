import {
  ListGroup,
  CheckboxEntry,
  isCheckboxEntryEdited,
} from '@bpmn-io/properties-panel';
import { is, isAny } from 'bpmn-js/lib/util/ModelUtil';
import scriptGroup, { SCRIPT_TYPE } from './SpiffScriptGroup';
import {
  ServiceTaskParameterArray,
  ServiceTaskOperatorSelect, ServiceTaskResultTextInput,
} from './SpiffExtensionServiceProperties';
import {OPTION_TYPE, spiffExtensionOptions, SpiffExtensionSelect} from './SpiffExtensionSelect';
import {SpiffExtensionLaunchButton} from './SpiffExtensionLaunchButton';
import {SpiffExtensionTextArea} from './SpiffExtensionTextArea';
import {SpiffExtensionTextInput} from './SpiffExtensionTextInput';
import {SpiffExtensionCheckboxEntry} from './SpiffExtensionCheckboxEntry';
import {hasEventDefinition} from 'bpmn-js/lib/util/DiUtil';
import { PropertyDescription } from 'bpmn-js-properties-panel/';
import {setExtensionValue} from "../extensionHelpers";

const LOW_PRIORITY = 500;

export default function ExtensionsPropertiesProvider(
  propertiesPanel,
  translate,
  moddle,
  commandStack,
  elementRegistry,
) {
  this.getGroups = function (element) {
    return function (groups) {
      if (is(element, 'bpmn:ScriptTask')) {
        groups.push(
          createScriptGroup(element, translate, moddle, commandStack)
        );
      } else if (
        isAny(element, ['bpmn:Task', 'bpmn:CallActivity', 'bpmn:SubProcess'])
      ) {
        groups.push(preScriptPostScriptGroup(element, translate, moddle, commandStack));
      }
      if (is(element, 'bpmn:UserTask')) {
        groups.push(createUserGroup(element, translate, moddle, commandStack));
      }

      if (is(element, 'bpmn:BusinessRuleTask')) {
        groups.push(
          createBusinessRuleGroup(element, translate, moddle, commandStack)
        );
      }
      if (
        isAny(element, [
          'bpmn:ManualTask',
          'bpmn:UserTask',
          'bpmn:ServiceTask',
          'bpmn:EndEvent',
          'bpmn:ScriptTask',
          'bpmn:IntermediateCatchEvent',
          'bpmn:CallActivity',
          'bpmn:SubProcess',
        ])
      ) {
        groups.push(
          createUserInstructionsGroup(element, translate, moddle, commandStack)
        );
      }
      if (
        isAny(element, [
          'bpmn:ManualTask',
          'bpmn:UserTask',
        ])
      ) {
        groups.push(
          createAllowGuestGroup(element, translate, moddle, commandStack)
        );
      }
      if (
        is(element, 'bpmn:BoundaryEvent') &&
        hasEventDefinition(element, 'bpmn:SignalEventDefinition') &&
        isAny(element.businessObject.attachedToRef, ['bpmn:ManualTask', 'bpmn:UserTask'])
      ) {
        groups.push(
          createSignalButtonGroup(element, translate, moddle, commandStack)
        );
      }
      if (is(element, 'bpmn:ServiceTask')) {
        groups.push(
          createServiceGroup(element, translate, moddle, commandStack)
        );
      }

      return groups;
    };
  };
  propertiesPanel.registerProvider(LOW_PRIORITY, this);
}

ExtensionsPropertiesProvider.$inject = [
  'propertiesPanel',
  'translate',
  'moddle',
  'commandStack',
  'elementRegistry',
];

/**
 * Adds a group to the properties panel for the script task that allows you
 * to set the script.
 * @param element
 * @param translate
 * @returns The components to add to the properties panel. */
function createScriptGroup(element, translate, moddle, commandStack) {
  return {
    id: 'spiff_script',
    label: translate('Script'),
    entries: scriptGroup({
      element,
      moddle,
      scriptType: SCRIPT_TYPE.bpmn,
      label: 'Script',
      description: 'Code to execute.',
      translate,
      commandStack,
    }),
  };
}

/**
 * Adds a section to the properties' panel for NON-Script tasks, so that
 * you can define a pre-script and a post-script for modifying data as it comes and out.
 * @param element
 * @param translate
 * @param moddle  For altering the underlying XML File.
 * @returns The components to add to the properties panel.
 */
function preScriptPostScriptGroup(element, translate, moddle, commandStack) {
  const entries = [
    ...scriptGroup({
      element,
      moddle,
      commandStack,
      translate,
      scriptType: SCRIPT_TYPE.pre,
      label: 'Pre-Script',
      description: 'code to execute prior to this task.',
    }),
    ...scriptGroup({
      element,
      moddle,
      commandStack,
      translate,
      scriptType: SCRIPT_TYPE.post,
      label: 'Post-Script',
      description: 'code to execute after this task.',
    }),
  ];
  const loopCharacteristics = element.businessObject.loopCharacteristics;
  if (typeof(loopCharacteristics) !== 'undefined') {
    entries.push({
      id: 'scriptValence',
      component: ScriptValenceCheckbox,
      isEdited: isCheckboxEntryEdited,
      commandStack,
    });
  }
  return {
    id: 'spiff_pre_post_scripts',
    label: translate('Pre/Post Scripts'),
    entries: entries,
  };
}

function ScriptValenceCheckbox(props) {

  const { element, commandStack } = props;

  const getValue = () => {
    return element.businessObject.loopCharacteristics.scriptsOnInstances;
  };

  const setValue = (value) => {
    const loopCharacteristics = element.businessObject.loopCharacteristics;
    loopCharacteristics.scriptsOnInstances = value || undefined;
    commandStack.execute('element.updateModdleProperties', {
      element,
      moddleElement: loopCharacteristics,
    });
  };

  return CheckboxEntry({
    element,
    id: 'selectScriptValence',
    label: 'Run scripts on instances',
    description: 'By default, scripts will attach to the multiinstance task',
    getValue,
    setValue,
  });
}

/**
 * Create a group on the main panel with a select box (for choosing the Data Object to connect)
 * @param element
 * @param translate
 * @param moddle
 * @returns entries
 */
function createUserGroup(element, translate, moddle, commandStack) {

  const updateExtensionProperties = (element, name, value, moddle, commandStack) => {
    const uiName = value.replace('schema\.json', 'uischema\.json')
    setExtensionValue(element, 'formJsonSchemaFilename', value, moddle, commandStack);
    setExtensionValue(element, 'formUiSchemaFilename', uiName, moddle, commandStack);
    const matches = spiffExtensionOptions[OPTION_TYPE.json_schema_files].filter((opt) => opt.value === value);
    if (matches.length === 0) {
      spiffExtensionOptions[OPTION_TYPE.json_schema_files].push({label: value, value: value});
    }
  }

  return {
    id: 'user_task_properties',
    label: translate('Web Form (with Json Schemas)'),
    entries: [
      {
        element,
        moddle,
        commandStack,
        component: SpiffExtensionSelect,
        optionType: OPTION_TYPE.json_schema_files,
        name: 'formJsonSchemaFilename',
        label: translate('JSON Schema Filename'),
        description: translate('Form Description (RSJF)'),
      },
      {
        component: SpiffExtensionLaunchButton,
        element,
        moddle,
        commandStack,
        name: 'formJsonSchemaFilename',
        label: translate('Launch Editor'),
        event: 'spiff.file.edit',
        listenEvent: 'spiff.jsonSchema.update',
        listenFunction: updateExtensionProperties,
        description: translate('Edit the form schema')
      },
    ],
  };
}

/**
 * Select and launch for Business Rules
 *
 * @param element
 * @param translate
 * @param moddle
 * @param commandStack
 * @returns {{entries: [{moddle, component: ((function(*): preact.VNode<any>)|*), name: string, description, label, commandStack, element},{component: ((function(*): preact.VNode<any>)|*), name: string, description, label, event: string, element}], id: string, label}}
 */
function createBusinessRuleGroup(element, translate, moddle, commandStack) {
  return {
    id: 'business_rule_properties',
    label: translate('Business Rule Properties'),
    entries: [
      {
        element,
        moddle,
        commandStack,
        component: SpiffExtensionSelect,
        optionType: OPTION_TYPE.dmn_files,
        name: 'spiffworkflow:CalledDecisionId',
        label: translate('Select Decision Table'),
        description: translate('Select a decision table from the list'),
      },
      {
        element,
        component: SpiffExtensionLaunchButton,
        name: 'spiffworkflow:CalledDecisionId',
        label: translate('Launch Editor'),
        event: 'spiff.dmn.edit',
        description: translate('Modify the Decision Table'),
      },
    ],
  };
}

/**
 * Create a group on the main panel with a text box (for choosing the information to display to the user)
 * @param element
 * @param translate
 * @param moddle
 * @returns entries
 */
function createUserInstructionsGroup (
  element,
  translate,
  moddle,
  commandStack
) {
  return {
    id: 'instructions',
    label: translate('Instructions'),
    entries: [
      {
        element,
        moddle,
        commandStack,
        component: SpiffExtensionTextArea,
        name: 'spiffworkflow:InstructionsForEndUser',
        label: 'Instructions',
        description: 'Displayed above user forms or when this task is executing.',
      },
      {
        element,
        moddle,
        commandStack,
        component: SpiffExtensionLaunchButton,
        name: 'spiffworkflow:InstructionsForEndUser',
        label: translate('Launch Editor'),
        event: 'spiff.markdown.edit',
        listenEvent: 'spiff.markdown.update',
        description: translate('Edit the form schema'),
      }
    ],
  };
}

/**
 * Create a group on the main panel with a text box (for choosing the information to display to the user)
 * @param element
 * @param translate
 * @param moddle
 * @returns entries
 */
function createAllowGuestGroup (
  element,
  translate,
  moddle,
  commandStack
) {
  return {
    id: 'allow_guest_user',
    label: translate('Guest options'),
    entries: [
      {
        element,
        moddle,
        commandStack,
        component: SpiffExtensionCheckboxEntry,
        name: 'spiffworkflow:AllowGuest',
        label: 'Guest can complete this task',
        description: 'Allow a guest user to complete this task without logging in. They will not be allowed to do anything but submit this task. If another task directly follows it that allows guest access, they could also complete that task.',
      },
      {
        element,
        moddle,
        commandStack,
        component: SpiffExtensionTextArea,
        name: 'spiffworkflow:GuestConfirmation',
        label: 'Guest confirmation',
        description: 'This is markdown that is displayed to the user after they complete the task. If this is filled out then the user will not be able to complete additional tasks without a new link to the next task.',
      },
      {
        element,
        moddle,
        commandStack,
        component: SpiffExtensionLaunchButton,
        name: 'spiffworkflow:GuestConfirmation',
        label: translate('Launch Editor'),
        event: 'spiff.markdown.edit',
        listenEvent: 'spiff.markdown.update',
      }
    ],
  };
}

/**
 * Create a group on the main panel with a text box for specifying a
 * a Button Label that is associated with a signal event.)
 * @param element
 * @param translate
 * @param moddle
 * @returns entries
 */
function createSignalButtonGroup (
  element,
  translate,
  moddle,
  commandStack
) {
  let description =
    <p style={{maxWidth : "330px"}}> If attached to a user/manual task, setting this value will display a button which a user can click to immediately fire this signal event.
    </p>
  return {
    id: 'signal_button',
    label: translate('Button'),
    entries: [
      {
        element,
        moddle,
        commandStack,
        component: SpiffExtensionTextInput,
        name: 'spiffworkflow:SignalButtonLabel',
        label: 'Button Label',
        description: description
      },
    ],
  };
}


/**
 * Create a group on the main panel with a text box (for choosing the dmn to connect)
 * @param element
 * @param translate
 * @param moddle
 * @returns entries
 */
function createServiceGroup(element, translate, moddle, commandStack) {
  return {
    id: 'service_task_properties',
    label: translate('Spiffworkflow Service Properties'),
    entries: [
      {
        element,
        moddle,
        commandStack,
        component: ServiceTaskOperatorSelect,
        translate,
      },
      {
        element,
        moddle,
        commandStack,
        component: ServiceTaskResultTextInput,
        translate,
      },
      {
        id: 'serviceTaskParameters',
        label: translate('Parameters'),
        component: ListGroup,
        ...ServiceTaskParameterArray({
          element,
          moddle,
          translate,
          commandStack
        }),
      },
    ],
  };
}
