import { is } from 'bpmn-js/lib/util/ModelUtil';

/**
 * loops up until it can find the root.
 * @param element
 */
export function getRoot(businessObject, moddle) {
  // HACK: get the root element. need a more formal way to do this
  if (moddle) {
    for (const elementId in moddle.ids._seed.hats) {
      if (elementId.startsWith('Definitions_')) {
        return moddle.ids._seed.hats[elementId];
      }
    }
  } else {
    // todo: Do we want businessObject to be a shape or moddle object?
    if (businessObject.$type === 'bpmn:Definitions') {
      return businessObject;
    }
    if (typeof businessObject.$parent !== 'undefined') {
      return getRoot(businessObject.$parent);
    }
  }
  return businessObject;
}

export function isMessageElement(shapeElement) {
  return (
    is(shapeElement, 'bpmn:SendTask') ||
    is(shapeElement, 'bpmn:ReceiveTask') ||
    isMessageEvent(shapeElement)
  );
}

export function isMessageEvent(shapeElement) {
  const { eventDefinitions } = shapeElement.businessObject;
  if (eventDefinitions && eventDefinitions[0]) {
    return eventDefinitions[0].$type === 'bpmn:MessageEventDefinition';
  }
  return false;
}

export function canReceiveMessage(shapeElement) {
  if (is(shapeElement, 'bpmn:ReceiveTask')) {
    return true;
  }
  if (isMessageEvent(shapeElement)) {
    return (
      is(shapeElement, 'bpmn:StartEvent') || is(shapeElement, 'bpmn:CatchEvent')
    );
  }
  return false;
}

export function getMessageRefElement(shapeElement) {
  if (isMessageEvent(shapeElement)) {
    const messageEventDefinition =
      shapeElement.businessObject.eventDefinitions[0];
    if (messageEventDefinition && messageEventDefinition.messageRef) {
      return messageEventDefinition.messageRef;
    }
  } else if (
    isMessageElement(shapeElement) &&
    shapeElement.businessObject.messageRef
  ) {
    return shapeElement.businessObject.messageRef;
  }
  return null;
}

export function findCorrelationKeyForCorrelationProperty(shapeElement, moddle) {
  const correlationKeyElements = findCorrelationKeys(shapeElement, moddle);
  for (const cke of correlationKeyElements) {
    if (cke.correlationPropertyRef) {
      for (const correlationPropertyRef of cke.correlationPropertyRef) {
        if (correlationPropertyRef.id === shapeElement.id) {
          return cke;
        }
      }
    }
  }
  return null;
}

export function findCorrelationPropertiesAndRetrievalExpressionsForMessage(
  shapeElement
) {
  const formalExpressions = [];
  const messageRefElement = getMessageRefElement(shapeElement);
  if (messageRefElement) {
    const root = getRoot(shapeElement.businessObject);
    if (root.$type === 'bpmn:Definitions') {
      for (const childElement of root.rootElements) {
        if (childElement.$type === 'bpmn:CorrelationProperty') {
          const retrievalExpression =
            getRetrievalExpressionFromCorrelationProperty(
              childElement,
              messageRefElement
            );
          if (retrievalExpression) {
            const formalExpression = {
              correlationPropertyModdleElement: childElement,
              correlationPropertyRetrievalExpressionModdleElement:
                retrievalExpression,
            };
            formalExpressions.push(formalExpression);
          }
        }
      }
    }
  }
  return formalExpressions;
}

export function getMessageElementForShapeElement(shapeElement) {
  const { businessObject } = shapeElement;
  const taskMessage = getMessageRefElement(shapeElement);
  const messages = findMessageModdleElements(businessObject);
  if (taskMessage) {
    for (const message of messages) {
      if (message.id === taskMessage.id) {
        return message;
      }
    }
  }
  return null;
}

function getRetrievalExpressionFromCorrelationProperty(
  correlationProperty,
  message
) {
  if (correlationProperty.correlationPropertyRetrievalExpression) {
    for (const retrievalExpression of correlationProperty.correlationPropertyRetrievalExpression) {
      if (
        retrievalExpression.$type ===
          'bpmn:CorrelationPropertyRetrievalExpression' &&
        retrievalExpression.messageRef &&
        retrievalExpression.messageRef.id === message.id
      ) {
        return retrievalExpression;
      }
    }
  }
  return null;
}

export function findCorrelationProperties(businessObject, moddle) {
  const root = getRoot(businessObject, moddle);
  const correlationProperties = [];
  if (isIterable(root.rootElements)) {
    for (const rootElement of root.rootElements) {
      if (rootElement.$type === 'bpmn:CorrelationProperty') {
        correlationProperties.push(rootElement);
      }
    }
  }
  return correlationProperties;
}

function isIterable(obj) {
  // checks for null and undefined
  if (obj == null) {
    return false;
  }
  return typeof obj[Symbol.iterator] === 'function';
}

export function findCorrelationKeys(businessObject, moddle) {
  const root = getRoot(businessObject, moddle);
  const correlationKeys = [];
  if (root.rootElements) {
    for (const rootElement of root.rootElements) {
      if (rootElement.$type === 'bpmn:Collaboration') {
        const currentKeys = rootElement.correlationKeys;
        for (const correlationKey in currentKeys) {
          const currentCorrelation = rootElement.correlationKeys[correlationKey];
          correlationKeys.push(currentCorrelation);
        }
      }
    }
  }
  return correlationKeys;
}

export function findMessageModdleElements(businessObject) {
  const messages = [];
  const root = getRoot(businessObject);
  if (root.rootElements) {
    for (const rootElement of root.rootElements) {
      if (rootElement.$type === 'bpmn:Message') {
        messages.push(rootElement);
      }
    }
  }
  return messages;
}
