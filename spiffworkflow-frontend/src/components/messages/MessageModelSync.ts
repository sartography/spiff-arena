import {
  areCorrelationPropertiesInSync,
  findNearestAncestorLocation,
} from './MessageHelper';

export type MessageModelResponseForSync = {
  identifier: string;
  location: string;
  correlation_properties: Array<{
    identifier: string;
    retrieval_expression: string;
  }>;
};

type ParsedBpmnMessage = {
  identifiers: string[];
  messageRef: string;
  correlationProperties: Array<{
    id: string;
    retrievalExpression: string;
  }>;
};

const localNameEquals = (element: Element, localName: string) => {
  return (
    element.localName === localName || element.nodeName.endsWith(localName)
  );
};

const childTextByLocalName = (element: Element, localName: string) => {
  const matchingChild = Array.from(element.children).find((child) =>
    localNameEquals(child, localName),
  );
  return matchingChild?.textContent?.trim() || '';
};

const uniqueValues = (values: Array<string | null | undefined>) => {
  return Array.from(
    new Set(values.filter((value): value is string => !!value)),
  );
};

const parseBpmnMessages = (bpmnXml: string): ParsedBpmnMessage[] => {
  const xmlDocument = new DOMParser().parseFromString(bpmnXml, 'text/xml');
  if (xmlDocument.querySelector('parsererror')) {
    return [];
  }

  const messageIdentifiersByReference: Record<string, string[]> = {};
  Array.from(xmlDocument.getElementsByTagName('*'))
    .filter((element) => localNameEquals(element, 'message'))
    .forEach((messageElement) => {
      const messageId = messageElement.getAttribute('id');
      const messageName = messageElement.getAttribute('name');
      const identifiers = uniqueValues([messageId, messageName]);
      if (messageId && identifiers.length > 0) {
        messageIdentifiersByReference[messageId] = identifiers;
      }
      if (messageName && identifiers.length > 0) {
        messageIdentifiersByReference[messageName] = identifiers;
      }
    });

  const messagesByIdentifier: Record<
    string,
    ParsedBpmnMessage['correlationProperties']
  > = {};
  Array.from(xmlDocument.getElementsByTagName('*'))
    .filter((element) =>
      localNameEquals(element, 'correlationPropertyRetrievalExpression'),
    )
    .forEach((retrievalExpressionElement) => {
      const messageRef = retrievalExpressionElement.getAttribute('messageRef');
      if (!messageRef) {
        return;
      }

      const correlationProperty = retrievalExpressionElement.parentElement;
      const correlationPropertyId = correlationProperty?.getAttribute('id');
      if (!correlationPropertyId) {
        return;
      }

      const retrievalExpression =
        childTextByLocalName(retrievalExpressionElement, 'messagePath') ||
        childTextByLocalName(retrievalExpressionElement, 'formalExpression');
      const identifiers = messageIdentifiersByReference[messageRef] || [
        messageRef,
      ];
      identifiers.forEach((identifier) => {
        if (!messagesByIdentifier[identifier]) {
          messagesByIdentifier[identifier] = [];
        }
        messagesByIdentifier[identifier].push({
          id: correlationPropertyId,
          retrievalExpression,
        });
      });
    });

  return Object.entries(messagesByIdentifier).map(
    ([identifier, correlationProperties]) => {
      const identifiers = messageIdentifiersByReference[identifier] || [
        identifier,
      ];
      return {
        identifiers,
        messageRef: identifiers[0],
        correlationProperties,
      };
    },
  );
};

const matchingMessageModel = (
  parsedMessage: ParsedBpmnMessage,
  currentLocation: string,
  messageModels: MessageModelResponseForSync[],
) => {
  const matchingModels = messageModels.filter((messageModel) =>
    parsedMessage.identifiers.includes(messageModel.identifier),
  );
  const nearestLocation = findNearestAncestorLocation(
    currentLocation,
    matchingModels.map((messageModel) => messageModel.location),
  );

  return (
    matchingModels.find(
      (messageModel) => messageModel.location === nearestLocation,
    ) || null
  );
};

export const hasUnsyncedBpmnMessage = (
  bpmnXml: string,
  currentLocation: string,
  messageModels: MessageModelResponseForSync[],
) => {
  const parsedMessages = parseBpmnMessages(bpmnXml);
  return parsedMessages.some((parsedMessage) => {
    const messageModel = matchingMessageModel(
      parsedMessage,
      currentLocation,
      messageModels,
    );
    if (!messageModel) {
      return true;
    }

    return !areCorrelationPropertiesInSync(
      {
        id: currentLocation,
        display_name: currentLocation,
        messages: {},
      },
      messageModel.identifier,
      parsedMessage.correlationProperties,
      currentLocation,
      [messageModel],
    );
  });
};

// eslint-disable-next-line sonarjs/no-clear-text-protocols
const bpmnNamespace = 'http://www.omg.org/spec/BPMN/20100524/MODEL';

const createBpmnElement = (xmlDocument: XMLDocument, localName: string) => {
  return xmlDocument.createElementNS(bpmnNamespace, `bpmn:${localName}`);
};

const getRootElement = (xmlDocument: XMLDocument) => {
  return xmlDocument.documentElement;
};

const getElementsByLocalName = (
  xmlDocument: XMLDocument,
  localName: string,
) => {
  return Array.from(xmlDocument.getElementsByTagName('*')).filter((element) =>
    localNameEquals(element, localName),
  );
};

const ensureCorrelationProperty = (
  xmlDocument: XMLDocument,
  propertyIdentifier: string,
) => {
  const existingProperty = getElementsByLocalName(
    xmlDocument,
    'correlationProperty',
  ).find((element) => element.getAttribute('id') === propertyIdentifier);
  if (existingProperty) {
    return existingProperty;
  }

  const correlationProperty = createBpmnElement(
    xmlDocument,
    'correlationProperty',
  );
  correlationProperty.setAttribute('id', propertyIdentifier);
  correlationProperty.setAttribute('name', propertyIdentifier);
  const rootElement = getRootElement(xmlDocument);
  const firstMessage = getElementsByLocalName(xmlDocument, 'message')[0];
  rootElement.insertBefore(correlationProperty, firstMessage || null);
  return correlationProperty;
};

const ensureRetrievalExpression = (
  xmlDocument: XMLDocument,
  correlationProperty: Element,
  messageRef: string,
) => {
  const existingExpression = Array.from(correlationProperty.children).find(
    (child) =>
      localNameEquals(child, 'correlationPropertyRetrievalExpression') &&
      child.getAttribute('messageRef') === messageRef,
  );
  if (existingExpression) {
    return existingExpression;
  }

  const retrievalExpression = createBpmnElement(
    xmlDocument,
    'correlationPropertyRetrievalExpression',
  );
  retrievalExpression.setAttribute('messageRef', messageRef);
  correlationProperty.appendChild(retrievalExpression);
  return retrievalExpression;
};

const setRetrievalExpressionValue = (
  xmlDocument: XMLDocument,
  retrievalExpression: Element,
  value: string,
) => {
  Array.from(retrievalExpression.children).forEach((child) => {
    if (
      localNameEquals(child, 'messagePath') ||
      localNameEquals(child, 'formalExpression')
    ) {
      retrievalExpression.removeChild(child);
    }
  });

  const messagePath = createBpmnElement(xmlDocument, 'messagePath');
  messagePath.textContent = value;
  retrievalExpression.appendChild(messagePath);
};

const removeUnusedRetrievalExpressions = (
  xmlDocument: XMLDocument,
  messageRef: string,
  activePropertyIds: Set<string>,
) => {
  getElementsByLocalName(xmlDocument, 'correlationProperty').forEach(
    (correlationProperty) => {
      Array.from(correlationProperty.children).forEach((child) => {
        if (
          localNameEquals(child, 'correlationPropertyRetrievalExpression') &&
          child.getAttribute('messageRef') === messageRef &&
          !activePropertyIds.has(correlationProperty.getAttribute('id') || '')
        ) {
          correlationProperty.removeChild(child);
        }
      });

      const hasRetrievalExpressions = Array.from(
        correlationProperty.children,
      ).some((child) =>
        localNameEquals(child, 'correlationPropertyRetrievalExpression'),
      );
      if (!hasRetrievalExpressions) {
        correlationProperty.parentElement?.removeChild(correlationProperty);
      }
    },
  );
};

export const syncBpmnMessagesToMessageModels = (
  bpmnXml: string,
  currentLocation: string,
  messageModels: MessageModelResponseForSync[],
) => {
  const xmlDocument = new DOMParser().parseFromString(bpmnXml, 'text/xml');
  if (xmlDocument.querySelector('parsererror')) {
    return bpmnXml;
  }

  parseBpmnMessages(bpmnXml).forEach((parsedMessage) => {
    const messageModel = matchingMessageModel(
      parsedMessage,
      currentLocation,
      messageModels,
    );
    if (!messageModel) {
      return;
    }

    const activePropertyIds = new Set(
      messageModel.correlation_properties.map(
        (property) => property.identifier,
      ),
    );
    messageModel.correlation_properties.forEach((property) => {
      const correlationProperty = ensureCorrelationProperty(
        xmlDocument,
        property.identifier,
      );
      const retrievalExpression = ensureRetrievalExpression(
        xmlDocument,
        correlationProperty,
        parsedMessage.messageRef,
      );
      setRetrievalExpressionValue(
        xmlDocument,
        retrievalExpression,
        property.retrieval_expression,
      );
    });
    removeUnusedRetrievalExpressions(
      xmlDocument,
      parsedMessage.messageRef,
      activePropertyIds,
    );
  });

  return new XMLSerializer().serializeToString(xmlDocument);
};
