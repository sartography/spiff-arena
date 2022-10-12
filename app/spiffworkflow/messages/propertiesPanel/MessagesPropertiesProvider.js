import { ListGroup, isTextFieldEntryEdited } from '@bpmn-io/properties-panel';
import { is } from 'bpmn-js/lib/util/ModelUtil';
import { CorrelationKeysArray } from './CorrelationKeysArray';
import { MessageSelect } from './MessageSelect';
import { MessagePayload } from './MessagePayload';
import { MessageVariable } from './MessageVariable';
import { CorrelationPropertiesArray } from './CorrelationPropertiesArray';
import { MessageCorrelationPropertiesArray } from './MessageCorrelationPropertiesArray';
import { MessageArray } from './MessageArray';
import { isMessageElement, canReceiveMessage } from '../MessageHelpers';

const LOW_PRIORITY = 500;

export default function MessagesPropertiesProvider(
  propertiesPanel,
  translate,
  moddle,
  commandStack,
  elementRegistry
) {
  this.getGroups = function getGroupsCallback(element) {
    return function pushGroup(groups) {
      if (is(element, 'bpmn:Collaboration')) {
        groups.push(
          ...createCollaborationGroup(
            element,
            translate,
            moddle,
            commandStack,
            elementRegistry
          )
        );
      } else if (isMessageElement(element)) {
        const messageIndex = findEntry(groups, 'message');
        if (messageIndex) {
          groups.splice(messageIndex, 1);
        }
        groups.push(
          createMessageGroup(
            element,
            translate,
            moddle,
            commandStack,
            elementRegistry
          )
        );
      }
      return groups;
    };
  };

  function findEntry(entries, entryId) {
    let entryIndex = null;
    entries.forEach(function (value, index) {
      if (value.id === entryId) {
        entryIndex = index;
      }
    });
    return entryIndex;
  }
  propertiesPanel.registerProvider(LOW_PRIORITY, this);
}

MessagesPropertiesProvider.$inject = [
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
function createCollaborationGroup(
  element,
  translate,
  moddle,
  commandStack,
  elementRegistry
) {
  return [
    {
      id: 'correlation_keys',
      label: translate('Correlation Keys'),
      component: ListGroup,
      ...CorrelationKeysArray({
        element,
        moddle,
        commandStack,
        elementRegistry,
        translate,
      }),
    },
    {
      id: 'correlation_properties',
      label: translate('Correlation Properties'),
      component: ListGroup,
      ...CorrelationPropertiesArray({
        element,
        moddle,
        commandStack,
        elementRegistry,
        translate,
      }),
    },
    {
      id: 'messages',
      label: translate('Messages'),
      component: ListGroup,
      ...MessageArray({
        element,
        moddle,
        commandStack,
        elementRegistry,
        translate,
      }),
    },
  ];
}

/**
 * Adds a group to the properties panel for editing messages for the SendTask
 * @param element
 * @param translate
 * @returns The components to add to the properties panel. */
function createMessageGroup(
  element,
  translate,
  moddle,
  commandStack,
  elementRegistry
) {
  const entries = [
    {
      id: 'selectMessage',
      element,
      component: MessageSelect,
      isEdited: isTextFieldEntryEdited,
      moddle,
      commandStack,
    },
  ];

  if (canReceiveMessage(element)) {
    entries.push({
      id: 'messageVariable',
      element,
      component: MessageVariable,
      isEdited: isTextFieldEntryEdited,
      moddle,
      commandStack,
    });
  } else {
    entries.push({
      id: 'messagePayload',
      element,
      component: MessagePayload,
      isEdited: isTextFieldEntryEdited,
      moddle,
      commandStack,
    });
  }

  entries.push({
    id: 'correlationProperties',
    label: translate('Correlation'),
    component: ListGroup,
    ...MessageCorrelationPropertiesArray({
      element,
      moddle,
      commandStack,
      elementRegistry,
      translate,
    }),
  });

  return {
    id: 'messages',
    label: translate('Message'),
    entries,
  };
}
