import { Form, Modal, Stack, TextInput } from '@carbon/react';
import { useState } from 'react';
import {
  CorrelationKey,
  CorrelationProperty,
  Message,
  ProcessGroup,
  RetrievalExpression,
} from '../../interfaces';

type OwnProps = {
  messageModel: Message;
  correlationKey?: CorrelationKey;
  processGroup: ProcessGroup;
  open: boolean;
  onClose: () => void;
  onSave: (updatedProcessGroup: ProcessGroup) => void;
};

export default function MessageModal({
  messageModel,
  correlationKey,
  processGroup,
  open,
  onClose,
  onSave,
}: OwnProps) {
  const getRetrievalExpression = (propertyName: string) => {
    if (processGroup.correlation_properties) {
      const cp: CorrelationProperty | undefined =
        processGroup.correlation_properties.find((ecp) => {
          return ecp.id === propertyName;
        });
      if (cp) {
        const re: RetrievalExpression | undefined =
          cp.retrieval_expressions.find((ere) => {
            return ere.message_ref === messageModel.id;
          });
        if (re) {
          return re.formal_expression;
        }
      }
    }
    return propertyName;
  };

  const getExpressions = () => {
    const expressions: Map<string, string> = new Map();
    if (correlationKey) {
      correlationKey.correlation_properties.forEach((prop: string) => {
        expressions.set(prop, getRetrievalExpression(prop));
      });
    }
    return expressions;
  };

  const [messageId, setMessageId] = useState<string>(messageModel.id);
  const [messageExpressions, setMessageExpressions] =
    useState<Map<string, string>>(getExpressions);
  const [invalidMessageName, setInvalidMessageName] = useState<boolean>(false);
  const [invalidExpressions, setInvalidExpressions] = useState<boolean>(false);

  let existingNames: string[] = [];
  if (processGroup.messages) {
    existingNames = processGroup.messages
      .filter((msg: Message) => {
        return msg.id !== messageModel.id;
      })
      .map((msg: Message) => {
        return msg.id;
      });
  }

  const validMessageName = (name: string): boolean => {
    return (
      name.length >= 3 &&
      /^[a-z0-9_]+$/.test(name) &&
      !existingNames.includes(name)
    );
  };

  const validExpression = (value: any): boolean => {
    return (
      (typeof value === 'string' || value instanceof String) && value.length > 0
    );
  };

  const updateMessageExpression = (prop: string, value: string) => {
    console.log('Updating message expression', prop, value);
    setMessageExpressions(new Map(messageExpressions.set(prop, value)));
    let ie = false;
    messageExpressions.forEach((v: string, _: string) => {
      console.log('valid expression', v, validExpression(v));
      if (!validExpression(v)) {
        ie = true;
      }
    });
    console.log('Setting invalid exressions to ', ie);
    setInvalidExpressions(ie);
  };

  const saveModel = () => {
    if (invalidMessageName || invalidExpressions) {
      console.log("Something isn't right!");
      return;
    }
    const updatedProcessGroup = JSON.parse(JSON.stringify(processGroup));

    // Update the message.id in this modified process group.
    if (!updatedProcessGroup.messages) {
      updatedProcessGroup.messages = [];
    }
    let message = updatedProcessGroup.messages?.find((msg: Message) => {
      return msg.id === messageModel.id;
    });
    if (!message) {
      updatedProcessGroup.messages.push(messageModel);
      message = messageModel;
    }
    message.id = messageId;
    console.log('messageExpressions', messageExpressions);

    // create or update the correlation properties
    correlationKey?.correlation_properties.forEach((prop: string) => {
      const value = messageExpressions.get(prop);
      console.log(
        'Updating correlation property',
        prop,
        value,
        'for',
        messageId
      );
      if (!value) {
        throw new Error(`No value for ${prop}`); // This should not happen, the form would be invalid.
      }
      let cp: CorrelationProperty | undefined =
        updatedProcessGroup.correlation_properties.find(
          (ecp: CorrelationProperty) => {
            return ecp.id === prop;
          }
        );
      if (!cp) {
        cp = { id: prop, retrieval_expressions: [] };
        updatedProcessGroup.correlation_properties.push(cp);
      }
      let re: RetrievalExpression | undefined = cp.retrieval_expressions.find(
        (ere) => {
          return ere.message_ref === messageModel.id;
        }
      );
      if (!re) {
        re = { message_ref: messageId, formal_expression: value };
        cp.retrieval_expressions.push(re);
      }
      re.formal_expression = value;
      re.message_ref = messageId;
    });
    console.log('updatedProcessGroup', updatedProcessGroup);
    onSave(updatedProcessGroup);
  };

  const retrievalExpressionFields = () => {
    if (correlationKey) {
      const fields = correlationKey.correlation_properties.map((prop: any) => {
        const label = `Extraction Expression for ${prop}`;
        const defaultValue = messageExpressions.get(prop) || prop;
        return (
          <TextInput
            id={prop}
            name={prop}
            labelText={label}
            defaultValue={defaultValue}
            errorMessage="Please enter a valid expression for all properties."
            invalid={invalidExpressions}
            onChange={(event: any) => {
              console.log('The Event Value is ', event.target.value);
              updateMessageExpression(prop, event.target.value);
            }}
          />
        );
      });
      return (
        <div className="retrievalExpressionsForm">
          <h2>Retrieval Expressions:</h2>
          The body of the message should be a JSON object that includes these
          properties. The value of each property will be extracted from the
          message and used to correlate the message to a running process.
          {fields}
        </div>
      );
    }
    return null;
  };

  const createMessageForm = () => {
    return (
      <Form onSubmit={onClose}>
        <Stack gap={5}>
          <TextInput
            id="message_name"
            name="message_name"
            placeholder="food_is_ready"
            invalidText='Must be unique, have a minimum of 3 letters, please use only letters and underscores, ie "food_is_ready"'
            invalid={invalidMessageName}
            labelText="Message Name*"
            defaultValue={messageId}
            onChange={(event: any) => {
              setMessageId(event.target.value);
              console.log(
                "It's changing to ",
                event.target.value,
                !validMessageName(event.target.value)
              );
              setInvalidMessageName(!validMessageName(event.target.value));
            }}
          />
          {retrievalExpressionFields()}
        </Stack>
      </Form>
    );
  };

  return (
    <Modal
      open={open}
      onRequestClose={onClose}
      modalHeading={`${messageModel.id}`}
      modalLabel="Details"
      primaryButtonText="Save"
      secondaryButtonText="Cancel"
      onSecondarySubmit={onClose}
      primaryButtonDisabled={invalidExpressions || invalidMessageName}
      onRequestSubmit={saveModel}
    >
      {createMessageForm()}
    </Modal>
  );
}
