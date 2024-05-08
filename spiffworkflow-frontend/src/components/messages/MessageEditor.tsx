import { useEffect, useState } from 'react';
import CustomForm from '../CustomForm';
import { ProcessGroup } from '../../interfaces';
import {
  unModifyProcessIdentifierForPathParam,
  setPageTitle,
} from '../../helpers';
import HttpService from '../../services/HttpService';
import { removeMessageFromProcessGroup } from './MessageHelper';

type OwnProps = {
  height: number;
  modifiedProcessGroupIdentifier: string;
  messageId: string;
};

export function MessageEditor({
  height,
  modifiedProcessGroupIdentifier,
  messageId,
}: OwnProps) {
  const [processGroup, setProcessGroup] = useState<ProcessGroup | null>(null);

  useEffect(() => {
    const processResult = (result: ProcessGroup) => {
      setProcessGroup(result);
      setPageTitle([result.display_name]);
    };
    HttpService.makeCallToBackend({
      path: `/process-groups/${modifiedProcessGroupIdentifier}`,
      successCallback: processResult,
    });
  }, [modifiedProcessGroupIdentifier, setProcessGroup]);

  const messageOptions = ['add new'];
  if (processGroup && processGroup.messages) {
    messageOptions.concat(processGroup.messages.map((message) => message.id));
  }

  const saveModel = (result: any) => {
    const { formData } = result;

    if (!processGroup) {
      return;
    }

    // Create an updated process group without the message being edited in the form.
    const updatedProcessGroup = removeMessageFromProcessGroup(
      messageId,
      processGroup
    );

    // Now add that message back in.
    if (!Array.isArray(updatedProcessGroup.messages)) {
      updatedProcessGroup.messages = [];
    }
    updatedProcessGroup.messages.push({ id: formData.messageId });

    if (!Array.isArray(updatedProcessGroup.correlation_properties)) {
      updatedProcessGroup.correlation_properties = [];
    }

    formData.correlation_properties.forEach((formProp: any) => {
      let prop = updatedProcessGroup.correlation_properties?.find(
        (p) => p.id === formProp.id
      );

      if (!prop) {
        prop = { id: formProp.id, retrieval_expressions: [] };
        updatedProcessGroup.correlation_properties?.push(prop);
      }
      prop.retrieval_expressions.push({
        message_ref: formData.messageId,
        formal_expression: formProp.retrievalExpression,
      });
    });

    const path = `/process-groups/${modifiedProcessGroupIdentifier}`;

    const handleProcessGroupUpdateResponse = (response: any) => {
      console.log('Successful post.', response);
    };

    HttpService.makeCallToBackend({
      path,
      successCallback: handleProcessGroupUpdateResponse,
      httpMethod: 'PUT',
      postBody: updatedProcessGroup,
    });
  };

  const schema = {
    type: 'object',
    required: ['processGroupIdentifier', 'messageId'],
    properties: {
      processGroupIdentifier: {
        type: 'string',
        title: 'Location',
        default: '/',
        description:
          'Only process models within this path will have access to this message.',
      },
      messageId: {
        type: 'string',
        title: 'Message Name',
        description:
          'The mesage name should contain no spaces or special characters',
      },
      correlation_properties: {
        type: 'array',
        title: 'Correlation Properties',
        items: {
          type: 'object',
          required: ['id', 'retrievalExpression'],
          properties: {
            id: {
              type: 'string',
              title: 'Property Name',
              description: '',
            },
            retrievalExpression: {
              type: 'string',
              title: 'Retrieval Expression',
              description:
                'This is how to extract the property from the body of the message',
            },
          },
        },
      },
      schema: {
        type: 'string',
        title: 'Json Schema',
        default: '{}',
        description: 'The message body must conform to this schema if defined.',
      },
    },
  };
  const uischema = {
    schema: {
      'ui:widget': 'textarea',
      'ui:rows': 5,
    },
    'ui:layout': [
      {
        processGroupIdentifier: { sm: 2, md: 4, lg: 8 },
        messageId: { sm: 2, md: 4, lg: 8 },
        schema: { sm: 4, md: 4, lg: 8 },
        correlation_properties: {
          sm: 4,
          md: 4,
          lg: 8,
          id: { sm: 2, md: 4, lg: 8 },
          extractionExpression: { sm: 2, md: 4, lg: 8 },
        },
      },
    ],
  };
  const formData = {
    processGroupIdentifier: unModifyProcessIdentifierForPathParam(
      modifiedProcessGroupIdentifier
    ),
    messageId,
  };

  // Make a form
  return (
    <CustomForm
      id={messageId}
      schema={schema}
      uiSchema={uischema}
      formData={formData}
      onSubmit={saveModel}
    >
      <div>
        <button type="submit">Save</button>
      </div>
    </CustomForm>
  );
}
