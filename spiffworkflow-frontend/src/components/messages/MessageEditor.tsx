import { useEffect, useState } from 'react';
import CustomForm from '../CustomForm';
import { ProcessGroup, Messages, RJSFFormObject } from '../../interfaces';
import {
  unModifyProcessIdentifierForPathParam,
  setPageTitle,
} from '../../helpers';
import HttpService from '../../services/HttpService';
import { getPropertiesForMessage } from './MessageHelper';

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
      console.log('result', result);
      setPageTitle([result.display_name]);
    };
    HttpService.makeCallToBackend({
      path: `/process-groups/${modifiedProcessGroupIdentifier}`,
      successCallback: processResult,
    });
  }, [modifiedProcessGroupIdentifier, setProcessGroup]);

  const messageOptions = ['add new'];
  // if (processGroup && processGroup.messages) {
  //   messageOptions.concat(processGroup.messages.map((message) => message.id));
  // }

  const saveModel = (formObject: RJSFFormObject) => {
    const { formData } = formObject;

    if (!processGroup) {
      return;
    }

    const newMessages: Messages = processGroup.messages || {};

    if (!(messageId in newMessages)) {
      newMessages[messageId] = { correlation_properties: {} };
    }

    (formData.correlation_properties || []).forEach((formProp: any) => {
      if (!(formProp.id in newMessages[messageId].correlation_properties)) {
        newMessages[messageId].correlation_properties[formProp.id] = {
          retrieval_expressions: [],
        };
      }
      if (
        !newMessages[messageId].correlation_properties[
          formProp.id
        ].retrieval_expressions.includes(formProp.retrievalExpression)
      ) {
        newMessages[messageId].correlation_properties[
          formProp.id
        ].retrieval_expressions.push(formProp.retrievalExpression);
      }
    });
    processGroup.messages = newMessages;

    const path = `/process-groups/${modifiedProcessGroupIdentifier}`;

    const handleProcessGroupUpdateResponse = (response: any) => {
      console.log('Successful post.', response);
    };

    HttpService.makeCallToBackend({
      path,
      successCallback: handleProcessGroupUpdateResponse,
      httpMethod: 'PUT',
      postBody: processGroup,
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
        description: 'The payload must conform to this schema if defined.',
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

  if (processGroup) {
    const correlationProperties = getPropertiesForMessage(
      { id: messageId },
      processGroup
    );
    const formData = {
      processGroupIdentifier: unModifyProcessIdentifierForPathParam(
        modifiedProcessGroupIdentifier
      ),
      messageId,
      correlation_properties: correlationProperties,
    };
    console.log('formData', formData);

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
  return null;
}
