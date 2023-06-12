import { ListGroup } from '@bpmn-io/properties-panel';
import { is, isAny } from 'bpmn-js/lib/util/ModelUtil';
import scriptGroup, { SCRIPT_TYPE } from './SpiffScriptGroup';
import {
  ServiceTaskParameterArray,
  ServiceTaskOperatorSelect, ServiceTaskResultTextInput,
} from './SpiffExtensionServiceProperties';
import {OPTION_TYPE, SpiffExtensionSelect} from './SpiffExtensionSelect';
import {SpiffExtensionLaunchButton} from './SpiffExtensionLaunchButton';
import {SpiffExtensionTextArea} from './SpiffExtensionTextArea';
import {SpiffExtensionTextInput} from './SpiffExtensionTextInput';
import {hasEventDefinition} from 'bpmn-js/lib/util/DiUtil';
import { PropertyDescription } from 'bpmn-js-properties-panel/';

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
  return {
    id: 'spiff_pre_post_scripts',
    label: translate('Pre/Post Scripts'),
    entries: [
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
    ],
  };
}

/**
 * Create a group on the main panel with a select box (for choosing the Data Object to connect)
 * @param element
 * @param translate
 * @param moddle
 * @returns entries
 */
function createUserGroup(element, translate, moddle, commandStack) {
  return {
    id: 'user_task_properties',
    label: translate('Web Form (with Json Schemas)'),
    entries: [
      {
        element,
        moddle,
        commandStack,
        component: SpiffExtensionSelect,
        optionType: OPTION_TYPE.json_files,
        name: 'formJsonSchemaFilename',
        label: translate('JSON Schema Filename'),
        description: translate('Form Description (RSJF)'),
      },
      {
        component: SpiffExtensionLaunchButton,
        element,
        name: 'formJsonSchemaFilename',
        label: translate('Launch Editor'),
        event: 'spiff.file.edit',
        description: translate('Edit the form description'),
      },
      {
        element,
        moddle,
        commandStack,
        component: SpiffExtensionSelect,
        optionType: OPTION_TYPE.json_files,
        label: translate('UI Schema Filename'),
        event: 'spiff.file.edit',
        description: translate('Rules for displaying the form. (RSJF Schema)'),
        name: 'formUiSchemaFilename',
      },
      {
        component: SpiffExtensionLaunchButton,
        element,
        name: 'formUiSchemaFilename',
        label: translate('Launch Editor'),
        event: 'spiff.file.edit',
        description: translate('Edit the form schema'),
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
        name: 'spiffworkflow:calledDecisionId',
        label: translate('Select Decision Table'),
        description: translate('Select a decision table from the list'),
      },
      {
        element,
        component: SpiffExtensionLaunchButton,
        name: 'spiffworkflow:calledDecisionId',
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
        name: 'spiffworkflow:instructionsForEndUser',
        label: 'Instructions',
        description: 'Displayed above user forms or when this task is executing.',
      },
      {
        element,
        moddle,
        commandStack,
        component: SpiffExtensionLaunchButton,
        name: 'spiffworkflow:instructionsForEndUser',
        label: translate('Launch Editor'),
        event: 'spiff.markdown.edit',
        listenEvent: 'spiff.markdown.update',
        description: translate('Edit the form schema'),
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
        name: 'spiffworkflow:signalButtonLabel',
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
