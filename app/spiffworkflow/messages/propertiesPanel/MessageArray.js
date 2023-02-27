import { useService } from 'bpmn-js-properties-panel';
import { TextFieldEntry } from '@bpmn-io/properties-panel';
import { getRoot, findMessageModdleElements } from '../MessageHelpers';
import { removeFirstInstanceOfItemFromArrayInPlace } from '../../helpers';

/**
 * Provides a list of data objects, and allows you to add / remove data objects, and change their ids.
 * @param props
 * @constructor
 */
export function MessageArray(props) {
  const { element, moddle, commandStack, translate } = props;

  const messageElements = findMessageModdleElements(element.businessObject);
  const items = messageElements.map((messageElement, index) => {
    const id = `messageElement-${index}`;
    return {
      id,
      label: messageElement.name,
      entries: messageGroup({
        idPrefix: id,
        element,
        messageElement,
        commandStack,
        translate,
      }),
      autoFocusEntry: id,
      remove: removeFactory({
        element,
        messageElement,
        commandStack,
        moddle,
      }),
    };
  });

  function add(event) {
    event.stopPropagation();
    if (element.type === 'bpmn:Collaboration') {
      const newMessageElement = moddle.create('bpmn:Message');
      const messageId = moddle.ids.nextPrefixed('Message_');
      newMessageElement.id = messageId;
      newMessageElement.name = messageId;
      const rootElement = getRoot(element.businessObject);
      const { rootElements } = rootElement;
      rootElements.push(newMessageElement);
      commandStack.execute('element.updateProperties', {
        element,
        properties: {},
      });
    }
  }

  return { items, add };
}

function removeMessageRefs(messageElement, moddleElement) {
  if (
    moddleElement.messageRef &&
    moddleElement.messageRef.id === messageElement.id
  ) {
    moddleElement.messageRef = null;
  } else if (moddleElement.correlationPropertyRetrievalExpression) {
    moddleElement.correlationPropertyRetrievalExpression.forEach((cpre) => {
      removeMessageRefs(messageElement, cpre);
    });
  } else if (moddleElement.flowElements) {
    moddleElement.flowElements.forEach((fe) => {
      removeMessageRefs(messageElement, fe);
    });
  } else if (moddleElement.eventDefinitions) {
    moddleElement.eventDefinitions.forEach((ed) => {
      removeMessageRefs(messageElement, ed);
    });
  }
}

function removeFactory(props) {
  const { element, messageElement, commandStack } = props;

  return function (event) {
    event.stopPropagation();
    const rootElement = getRoot(element.businessObject);
    const { rootElements } = rootElement;
    removeFirstInstanceOfItemFromArrayInPlace(rootElements, messageElement);
    rootElements.forEach((moddleElement) => {
      removeMessageRefs(messageElement, moddleElement);
    });
    commandStack.execute('element.updateProperties', {
      element,
      properties: {},
    });
  };
}

function messageGroup(props) {
  const { messageElement, commandStack, translate, idPrefix } = props;
  return [
    {
      id: `${idPrefix}-name`,
      component: MessageNameTextField,
      messageElement,
      commandStack,
      translate,
    },
  ];
}

function MessageIdTextField(props) {
  const { id, element, messageElement, commandStack, translate } = props;

  const debounce = useService('debounceInput');
  const setValue = (value) => {
    commandStack.execute('element.updateModdleProperties', {
      element,
      moddleElement: messageElement,
      properties: {
        id: value,
      },
    });
  };

  const getValue = () => {
    return messageElement.id;
  };

  return TextFieldEntry({
    element,
    id: `${id}-id-textField`,
    label: translate('ID'),
    getValue,
    setValue,
    debounce,
  });
}

function MessageNameTextField(props) {
  const { id, element, messageElement, commandStack, translate } = props;

  const debounce = useService('debounceInput');
  const setValue = (value) => {
    commandStack.execute('element.updateModdleProperties', {
      element,
      moddleElement: messageElement,
      properties: {
        name: value,
      },
    });
  };

  const getValue = () => {
    return messageElement.name;
  };

  return TextFieldEntry({
    element,
    id: `${id}-name-textField`,
    label: translate('Name'),
    getValue,
    setValue,
    debounce,
  });
}
