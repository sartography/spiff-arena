import { ProcessGroup } from '../../interfaces';

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

export const convertCorrelationPropertiesToRJSF = (
  messageId: string,
  processGroup: ProcessGroup,
) => {
  const correlationProperties = getPropertiesForMessage(
    messageId,
    processGroup,
  );
  const correlationPropertiesToUse = correlationProperties || {};
  const returnArray: any = [];
  Object.keys(correlationPropertiesToUse).forEach((propIdentifier: string) => {
    const property = correlationPropertiesToUse[propIdentifier];
    return property.retrieval_expressions.forEach((retExp: string) => {
      returnArray.push({
        id: propIdentifier,
        retrievalExpression: retExp,
      });
    });
  });
  return returnArray;
};

export const mergeCorrelationProperties = (
  xmlProperties: any,
  apiProperties: any,
) => {
  const mergedProperties = xmlProperties ? [...xmlProperties] : [];

  apiProperties.forEach((apiProperty: any) => {
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

export const isCorrelationPropertiesInSync = (processGroup: ProcessGroup, messageId: string, messageProperties: any[]) => {

  const message = (processGroup.messages) ? processGroup.messages[messageId] : undefined;

  if (!message) {
    return false;
  }

  for (const property of messageProperties) {
    const correlationProperty = message.correlation_properties[property.id];

    if (!correlationProperty) {
      return false;
    }

    const localRetrievalExpression = (Array.isArray(property.retrievalExpression)) ? property.retrievalExpression[0] : property.retrievalExpression;

    if (!correlationProperty.retrieval_expressions.includes(localRetrievalExpression)) {
      return false;
    }
  }

  return true;
};
