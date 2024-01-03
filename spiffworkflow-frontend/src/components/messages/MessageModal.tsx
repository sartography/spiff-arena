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
  const [identifierInvalid, setIdentifierInvalid] = useState<boolean>(false);

  const updatedProcessGroup: ProcessGroup = JSON.parse(
    JSON.stringify(processGroup)
  );
  console.log('updatedProcessGroup', updatedProcessGroup);

  const findMessageInGroup = (): Message => {
    const message = updatedProcessGroup.messages?.find((msg: Message) => {
      return msg.id === messageModel.id;
    });
    if (message) {
      return message;
    }
    throw new Error(`Message ${messageModel.id} not found in group`);
  };
  const updatedMessage: Message = findMessageInGroup();

  const onMessageNameChange = (event: any) => {
    if (messageModel.id.length < 3 || !/^[a-z0-9_]+$/.test(messageModel.id)) {
      setIdentifierInvalid(true);
    } else {
      const originalId = updatedMessage.id;
      updatedMessage.id = event.target.value;
      if (updatedProcessGroup.correlation_properties) {
        updatedProcessGroup.correlation_properties.forEach(
          (prop: CorrelationProperty) => {
            prop.retrieval_expressions.forEach((re: any) => {
              if (re.message_ref === originalId) {
                console.log('updating message_ref', re);
                // eslint-disable-next-line no-param-reassign
                re.message_ref = updatedMessage.id;
              }
            });
          }
        );
      }
      console.log("updated Process Group name change", updatedProcessGroup);
    }
  };

  const updateRetrievalExpression = (prop: string, value: string) => {
    if (!updatedProcessGroup.correlation_properties) {
      updatedProcessGroup.correlation_properties = [];
    }
    let cp: CorrelationProperty | undefined =
      updatedProcessGroup.correlation_properties.find((ecp) => {
        return ecp.id === prop;
      });
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
      re = { message_ref: messageModel.id, formal_expression: value };
      cp.retrieval_expressions.push(re);
    }
    re.formal_expression = value;
  };

  const getRetrievalExpression = (propertyName: string) => {
    if (updatedProcessGroup.correlation_properties) {
      const cp: CorrelationProperty | undefined =
        updatedProcessGroup.correlation_properties.find((ecp) => {
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
    return '';
  };

  const retrievalExpressionFields = () => {
    if (correlationKey) {
      const fields = correlationKey.correlation_properties.map((prop: any) => {
        const label = `Extraction Expression for ${prop}`;
        const value = getRetrievalExpression(prop);
        return (
          <TextInput
            id={prop}
            name={prop}
            invalid={identifierInvalid}
            labelText={label}
            defaultValue={value}
            onChange={(event: any) => {
              updateRetrievalExpression(prop, event.target.value);
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
            invalidText='Minimum of 3 letters, please use only letters and underscores, ie "food_is_ready"'
            invalid={identifierInvalid}
            labelText="Message Name*"
            defaultValue={updatedMessage.id}
            onChange={onMessageNameChange}
          />
          {retrievalExpressionFields()}
        </Stack>
      </Form>
    );
  };

  const saveModel = () => {
    onSave(updatedProcessGroup);
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
      onRequestSubmit={saveModel}
    >
      {createMessageForm()}
    </Modal>
  );
}
