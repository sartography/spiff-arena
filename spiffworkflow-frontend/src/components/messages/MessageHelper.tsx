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
    returnArray.push({
      id: propIdentifier,
      retrievalExpression: property.retrieval_expression,
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

export const areCorrelationPropertiesInSync = (
  processGroup: ProcessGroup,
  messageId: string,
  messageProperties: any[],
) => {
  if (!messageId) {
    // About Message Creation
    return true;
  }

  const message = processGroup.messages
    ? processGroup.messages[messageId]
    : undefined;

  if (!message) {
    return false;
  }

  const localPropertyIds = messageProperties.map((property) => property.id);
  const processGroupPropertyIds = Object.keys(message.correlation_properties);

  // Check if all local properties exist in the process group data
  // TODO: fix the lint
  // eslint-disable-next-line
  for (const property of messageProperties) {
    const correlationProperty = message.correlation_properties[property.id];

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

  // Checking if all process group properties exist in the local xml
  // TODO: fix the lint
  // eslint-disable-next-line
  for (const propertyId of processGroupPropertyIds) {
    if (!localPropertyIds.includes(propertyId)) {
      return false;
    }
  }

  return true;
};
