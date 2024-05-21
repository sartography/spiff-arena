import { ProcessGroup } from '../../interfaces';

const arrayCompare = (array1: string[], array2: string[]) => {
  return (
    array1.length === array2.length &&
    array1.every((value, index) => value === array2[index])
  );
};

export const getPropertiesForMessage = (
  messageId: string,
  processGroup: ProcessGroup
) => {
  const message = (processGroup.messages || {})[messageId];
  if (message) {
    return message.correlation_properties;
  }
  return null;
};

export const convertCorrelationPropertiesToRJSF = (
  messageId: string,
  processGroup: ProcessGroup
) => {
  const correlationProperties = getPropertiesForMessage(
    messageId,
    processGroup
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
