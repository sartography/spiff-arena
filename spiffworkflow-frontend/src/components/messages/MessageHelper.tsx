import {
  CorrelationKey,
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
  message: Message,
  processGroup: ProcessGroup
) => {
  const properties: CorrelationProperty[] = [];
  if (processGroup.correlation_properties) {
    processGroup.correlation_properties.forEach((cp: CorrelationProperty) => {
      cp.retrieval_expressions.forEach((re: RetrievalExpression) => {
        if (re.message_ref === message.id) {
          properties.push(cp);
        }
      });
    });
  }
  return properties;
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

export const findMessagesForCorrelationKey = (
  processGroup: ProcessGroup,
  correlationKey?: CorrelationKey
): Message[] => {
  console.log('Find messages for CK', correlationKey);
  const messages: Message[] = [];
  if (processGroup.messages) {
    processGroup.messages.forEach((msg: Message) => {
      const correlationProperties = getPropertiesForMessage(msg, processGroup);
      const propIds: string[] = correlationProperties.map(
        (cp: CorrelationProperty) => {
          return cp.id;
        }
      );
      propIds.sort();
      if (correlationKey) {
        if (
          arrayCompare(propIds, correlationKey.correlation_properties.sort())
        ) {
          messages.push(msg);
        }
      } else if (propIds.length === 0) {
        messages.push(msg);
      }
    });
  }
  return messages;
};
