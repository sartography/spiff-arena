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
