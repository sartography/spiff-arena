export type CorrelationProperty = {
  retrieval_expression?: string;
};

export type MessageDefinition = {
  correlation_properties?: Record<string, CorrelationProperty>;
  schema?: Record<string, unknown>;
};

export type ProcessGroup = {
  display_name?: string;
  messages?: Record<string, MessageDefinition>;
};

export const getPropertiesForMessage = (
  messageId: string,
  processGroup: ProcessGroup,
) => {
  const message = (processGroup.messages || {})[messageId];
  if (message) {
    return message.correlation_properties;
  }
  return null;
};

export const convertCorrelationPropertiesToFormData = (
  messageId: string,
  processGroup: ProcessGroup,
) => {
  const correlationProperties = getPropertiesForMessage(
    messageId,
    processGroup,
  );
  const correlationPropertiesToUse = correlationProperties || {};
  const returnArray: Array<{ id: string; retrievalExpression?: string }> = [];
  Object.keys(correlationPropertiesToUse).forEach((propIdentifier: string) => {
    const property = correlationPropertiesToUse[propIdentifier];
    returnArray.push({
      id: propIdentifier,
      retrievalExpression: property.retrieval_expression,
    });
  });
  return returnArray;
};

export const mergeCorrelationProperties = (
  xmlProperties: Array<{ id: string; retrievalExpression?: string }> | null,
  apiProperties: Array<{ id: string; retrievalExpression?: string }>,
) => {
  const mergedProperties = xmlProperties ? [...xmlProperties] : [];

  apiProperties.forEach((apiProperty) => {
    const existingProperty = mergedProperties.find(
      (prop) => prop.id === apiProperty.id,
    );

    if (existingProperty) {
      existingProperty.retrievalExpression = apiProperty.retrievalExpression;
    } else {
      mergedProperties.push(apiProperty);
    }
  });

  return mergedProperties;
};

export const areCorrelationPropertiesInSync = (
  processGroup: ProcessGroup,
  messageId: string,
  messageProperties: Array<{ id: string; retrievalExpression?: string }>,
) => {
  if (!messageId) {
    return true;
  }

  const message = processGroup.messages
    ? processGroup.messages[messageId]
    : undefined;

  if (!message) {
    return false;
  }

  const localPropertyIds = messageProperties.map((property) => property.id);
  const processGroupPropertyIds = Object.keys(message.correlation_properties || {});

  for (const property of messageProperties) {
    const correlationProperty = message.correlation_properties
      ? message.correlation_properties[property.id]
      : undefined;

    if (!correlationProperty) {
      return false;
    }

    const localRetrievalExpression = Array.isArray(property.retrievalExpression)
      ? property.retrievalExpression[0]
      : property.retrievalExpression;

    if (correlationProperty.retrieval_expression !== localRetrievalExpression) {
      return false;
    }
  }

  for (const propertyId of processGroupPropertyIds) {
    if (!localPropertyIds.includes(propertyId)) {
      return false;
    }
  }

  return true;
};
