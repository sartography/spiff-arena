import { useEffect, useState } from 'react';
import CustomForm from '../CustomForm';
import {
  ProcessGroup,
  RJSFFormObject,
  MessageDefinition,
  CorrelationProperties,
} from '../../interfaces';
import {
  unModifyProcessIdentifierForPathParam,
  setPageTitle,
} from '../../helpers';
import HttpService from '../../services/HttpService';
import { convertCorrelationPropertiesToRJSF } from './MessageHelper';
import { Notification } from '../Notification';

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
  const [displaySaveMessageMessage, setDisplaySaveMessageMessage] =
    useState<boolean>(false);
  const [currentMessageId, setCurrentMessageId] = useState<string>();

  useEffect(() => {
    const processResult = (result: ProcessGroup) => {
      setProcessGroup(result);
      setCurrentMessageId(messageId);
      setPageTitle([result.display_name]);
    };
    HttpService.makeCallToBackend({
      path: `/process-groups/${modifiedProcessGroupIdentifier}`,
      successCallback: processResult,
    });
  }, [modifiedProcessGroupIdentifier, setProcessGroup]);

  const handleProcessGroupUpdateResponse = (response: ProcessGroup) => {
    setProcessGroup(response);
    setDisplaySaveMessageMessage(true);
  };

  const updateCorrelationPropertiesOnProcessGroup = (
    currentMessagesForId: MessageDefinition,
    formData: any
  ) => {
    const correlationProperties: CorrelationProperties = {
      ...currentMessagesForId.correlation_properties,
    };
    (formData.correlation_properties || []).forEach((formProp: any) => {
      if (!(formProp.id in correlationProperties)) {
        correlationProperties[formProp.id] = {
          retrieval_expressions: [],
        };
      }
      if (
        !correlationProperties[formProp.id].retrieval_expressions.includes(
          formProp.retrievalExpression
        )
      ) {
        correlationProperties[formProp.id].retrieval_expressions.push(
          formProp.retrievalExpression
        );
      }
    });

    Object.keys(currentMessagesForId.correlation_properties || []).forEach(
      (propId: string) => {
        const foundProp = (formData.correlation_properties || []).find(
          (formProp: any) => {
            return propId === formProp.id;
          }
        );
        if (!foundProp) {
          delete correlationProperties[propId];
        }
      }
    );
    return correlationProperties;
  };

  const updateProcessGroupWithMessages = (formObject: RJSFFormObject) => {
    const { formData } = formObject;

    if (!processGroup) {
      return;
    }

    // keep track of new and old message ids so we can handle renaming a message
    const newMessageId = formData.messageId;
    const oldMessageId = currentMessageId || newMessageId;

    const processGroupForUpdate = { ...processGroup };
    if (!processGroupForUpdate.messages) {
      processGroupForUpdate.messages = {};
    }
    const currentMessagesForId: MessageDefinition =
      (processGroupForUpdate.messages || {})[oldMessageId] || {};
    const updatedMessagesForId = { ...currentMessagesForId };

    const correlationProperties = updateCorrelationPropertiesOnProcessGroup(
      currentMessagesForId,
      formData
    );

    updatedMessagesForId.correlation_properties = correlationProperties;

    try {
    	updatedMessagesForId.schema = JSON.parse(formData.schema || '{}');
    } catch (e) {
      alert(`Invalid schema: ${e}`);
      return;
    }

    processGroupForUpdate.messages[newMessageId] = updatedMessagesForId;
    setCurrentMessageId(newMessageId);
    const path = `/process-groups/${modifiedProcessGroupIdentifier}`;
    HttpService.makeCallToBackend({
      path,
      successCallback: handleProcessGroupUpdateResponse,
      httpMethod: 'PUT',
      postBody: processGroupForUpdate,
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
    const correlationProperties = convertCorrelationPropertiesToRJSF(
      currentMessageId,
      processGroup
    );
    const jsonSchema = (processGroup.messages || {})[currentMessageId]?.schema || {};
    const formData = {
      processGroupIdentifier: unModifyProcessIdentifierForPathParam(
        modifiedProcessGroupIdentifier
      ),
      messageId: currentMessageId,
      correlation_properties: correlationProperties,
      schema: JSON.stringify(jsonSchema, null, 2),
    };

    // Make a form
    return (
      <>
        {displaySaveMessageMessage ? (
          <Notification
            title="Save successful"
            hideCloseButton
            timeout={4000}
            onClose={() => setDisplaySaveMessageMessage(false)}
          >
            Message has been saved
          </Notification>
        ) : null}
        <CustomForm
          id={currentMessageId}
          schema={schema}
          uiSchema={uischema}
          formData={formData}
          onSubmit={updateProcessGroupWithMessages}
          submitButtonText="Save"
        />
      </>
    );
  }
  return null;
}
