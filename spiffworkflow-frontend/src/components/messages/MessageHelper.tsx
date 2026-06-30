import { ProcessGroup } from '../../interfaces';

export const findNearestAncestorLocation = (
  currentLocation: string,
  candidateLocations: string[],
) => {
  const normalizedCurrentLocation = currentLocation.replace(/(^\/+|\/+$)/g, '');

  const matchingLocations = candidateLocations.filter((candidateLocation) => {
    const normalizedCandidate = candidateLocation.replace(/(^\/+|\/+$)/g, '');
    return (
      normalizedCurrentLocation === normalizedCandidate ||
      normalizedCurrentLocation.startsWith(`${normalizedCandidate}/`)
    );
  });

  if (matchingLocations.length === 0) {
    return null;
  }

  return matchingLocations.sort(
    (a: string, b: string) => b.length - a.length,
  )[0];
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
  currentLocation?: string,
  matchingMessageModels: Array<{
    location: string;
    correlation_properties: Array<{
      identifier: string;
      retrieval_expression: string;
    }>;
  }> = [],
) => {
  if (!messageId) {
    // About Message Creation
    return true;
  }

  let message = processGroup.messages
    ? processGroup.messages[messageId]
    : undefined;

  if (!message && currentLocation != null) {
    const nearestAncestorLocation = findNearestAncestorLocation(
      currentLocation,
      matchingMessageModels.map((messageModel) => messageModel.location),
    );
    const matchingMessageModel = matchingMessageModels.find(
      (messageModel) => messageModel.location === nearestAncestorLocation,
    );
    if (matchingMessageModel) {
      message = {
        correlation_properties:
          matchingMessageModel.correlation_properties.reduce(
            (
              result: Record<string, { retrieval_expression: string }>,
              property,
            ) => {
              result[property.identifier] = {
                retrieval_expression: property.retrieval_expression,
              };
              return result;
            },
            {},
          ),
      };
    }
  }

  if (!message) {
    return false;
  }

  const localPropertyIds = messageProperties.map((property) => property.id);
  const processGroupPropertyIds = Object.keys(message.correlation_properties);

  // Check if all local properties exist in the process group data
  // TODO: fix the lint

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

  for (const propertyId of processGroupPropertyIds) {
    if (!localPropertyIds.includes(propertyId)) {
      return false;
    }
  }

  return true;
};
