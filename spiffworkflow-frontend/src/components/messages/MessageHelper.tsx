import {
  CorrelationProperty,
  Message,
  ProcessGroup,
  RetrievalExpression,
} from '../../interfaces';

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

export const removeMessageFromProcessGroup = (
  messageId: string,
  processGroup: ProcessGroup
): ProcessGroup => {
  const updatedProcessGroup = JSON.parse(JSON.stringify(processGroup));

  // Remove the original message and all it's properties
  if (updatedProcessGroup.messages) {
    updatedProcessGroup.messages = updatedProcessGroup.messages.filter(
      (m: Message) => {
        return m.id !== messageId;
      }
    );
  }

  if (updatedProcessGroup.correlation_properties) {
    updatedProcessGroup.correlation_properties.forEach(
      (prop: CorrelationProperty) => {
        // eslint-disable-next-line no-param-reassign
        prop.retrieval_expressions = prop.retrieval_expressions.filter(
          (re: RetrievalExpression) => {
            return re.message_ref !== messageId;
          }
        );
      }
    );
    updatedProcessGroup.correlation_properties =
      updatedProcessGroup.correlation_properties.filter(
        (prop: CorrelationProperty) => {
          return prop.retrieval_expressions.length > 0;
        }
      );
  }
  return processGroup;
};
