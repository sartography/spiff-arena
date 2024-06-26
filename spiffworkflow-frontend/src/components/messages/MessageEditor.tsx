import { useCallback, useEffect, useState } from 'react';
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
import {
  areCorrelationPropertiesInSync,
  convertCorrelationPropertiesToRJSF,
  mergeCorrelationProperties,
} from './MessageHelper';
import { Notification } from '../Notification';

type OwnProps = {
  modifiedProcessGroupIdentifier: string;
  elementId: string;
  messageId: string;
  messageEvent: any;
  correlationProperties: any;
};

export function MessageEditor({
  modifiedProcessGroupIdentifier,
  messageId,
  messageEvent,
  correlationProperties,
  elementId,
}: OwnProps) {
  const [processGroup, setProcessGroup] = useState<ProcessGroup | null>(null);
  const [currentFormData, setCurrentFormData] = useState<any>(null);
  const [displaySaveMessageMessage, setDisplaySaveMessageMessage] =
    useState<boolean>(false);
  const [currentMessageId, setCurrentMessageId] = useState<string | null>(null);
  const [isSynced, setSynced] = useState<boolean>(true);

  const updateCorrelationPropertiesOnProcessGroup = useCallback(
    (currentMessagesForId: MessageDefinition, formData: any) => {
      const newCorrelationProperties: CorrelationProperties = {
        ...currentMessagesForId.correlation_properties,
      };
      (formData.correlation_properties || []).forEach((formProp: any) => {
        newCorrelationProperties[formProp.id] = {
          retrieval_expression: formProp.retrievalExpression,
        };
      });
      Object.keys(currentMessagesForId.correlation_properties || []).forEach(
        (propId: string) => {
          const foundProp = (formData.correlation_properties || []).find(
            (formProp: any) => {
              return propId === formProp.id;
            },
          );
          if (!foundProp) {
            delete newCorrelationProperties[propId];
          }
        },
      );
      return newCorrelationProperties;
    },
    [],
  );

  const handleProcessGroupUpdateResponse = useCallback(
    (
      response: ProcessGroup,
      messageIdentifier: string,
      updatedMessagesForId: MessageDefinition,
    ) => {
      setProcessGroup(response);
      setDisplaySaveMessageMessage(true);
      messageEvent.eventBus.fire('spiff.add_message.returned', {
        name: messageIdentifier,
        correlation_properties: updatedMessagesForId.correlation_properties,
        elementId,
      });
      setSynced(true);
    },
    [elementId, messageEvent.eventBus],
  );

  const updateProcessGroupWithMessages = useCallback(
    (formObject: RJSFFormObject) => {
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

      const newCorrelationProperties =
        updateCorrelationPropertiesOnProcessGroup(
          currentMessagesForId,
          formData,
        );

      updatedMessagesForId.correlation_properties = newCorrelationProperties;

      try {
        updatedMessagesForId.schema = JSON.parse(formData.schema || '{}');
      } catch (e) {
        // TODO: display error in a tag like we normally do
        // eslint-disable-next-line no-alert
        alert(`Invalid schema: ${e}`);
        return;
      }

      processGroupForUpdate.messages[newMessageId] = updatedMessagesForId;
      setCurrentMessageId(newMessageId);
      const path = `/process-groups/${modifiedProcessGroupIdentifier}`;
      HttpService.makeCallToBackend({
        path,
        successCallback: (response: ProcessGroup) =>
          handleProcessGroupUpdateResponse(
            response,
            newMessageId,
            updatedMessagesForId,
          ),
        httpMethod: 'PUT',
        postBody: processGroupForUpdate,
      });
    },
    [
      currentMessageId,
      handleProcessGroupUpdateResponse,
      modifiedProcessGroupIdentifier,
      processGroup,
      updateCorrelationPropertiesOnProcessGroup,
    ],
  );

  useEffect(() => {
    const setInitialFormData = (newProcessGroup: ProcessGroup) => {
      let newCorrelationProperties = convertCorrelationPropertiesToRJSF(
        messageId,
        newProcessGroup,
      );
      newCorrelationProperties = mergeCorrelationProperties(
        correlationProperties,
        newCorrelationProperties,
      );
      const jsonSchema =
        (newProcessGroup.messages || {})[messageId]?.schema || {};
      const newFormData = {
        processGroupIdentifier: unModifyProcessIdentifierForPathParam(
          modifiedProcessGroupIdentifier,
        ),
        messageId,
        correlation_properties: newCorrelationProperties,
        schema: JSON.stringify(jsonSchema, null, 2),
      };
      setCurrentFormData(newFormData);
    };
    const processResult = (result: ProcessGroup) => {
      const newIsSynced = areCorrelationPropertiesInSync(
        result,
        messageId,
        correlationProperties,
      );
      setSynced(newIsSynced);
      setProcessGroup(result);
      setCurrentMessageId(messageId);
      setPageTitle([result.display_name]);
      setInitialFormData(result);
    };
    HttpService.makeCallToBackend({
      path: `/process-groups/${modifiedProcessGroupIdentifier}`,
      successCallback: processResult,
    });
  }, [modifiedProcessGroupIdentifier, correlationProperties, messageId]);

  const schema = {
    type: 'object',
    required: ['processGroupIdentifier', 'messageId'],
    properties: {
      processGroupIdentifier: {
        type: 'string',
        title: 'Location',
        default: '/',
        pattern: '^[\\/\\w-]+$',
        validationErrorMessage:
          'must contain only alphanumeric characters, "/", underscores, or hyphens',
        description:
          'Only process models within this path will have access to this message.',
      },
      messageId: {
        type: 'string',
        title: 'Message Name',
        pattern: '^[\\w-]+$',
        validationErrorMessage:
          'must contain only alphanumeric characters, underscores, or hyphens',
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
              pattern: '^[\\w-]+$',
              validationErrorMessage:
                'The property name should contain no spaces or special characters',
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
      'ui:options': { validateJson: true },
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

  const updateFormData = (formObject: any) => {
    setCurrentFormData(formObject.formData);
  };

  if (processGroup && currentFormData) {
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
        {!isSynced && !displaySaveMessageMessage ? (
          <Notification
            title="Please Save the current message configuration"
            type="warning"
            hideCloseButton
            timeout={4000}
            onClose={() => setDisplaySaveMessageMessage(false)}
          >
            There is a difference between the message properties in this process
            model and the shared message data stored with the process group.
            Updating the message properties by saving is recommended to ensure
            data consistency
          </Notification>
        ) : null}
        <CustomForm
          id={currentMessageId || ''}
          key={currentMessageId || ''}
          schema={schema}
          uiSchema={uischema}
          formData={currentFormData}
          onSubmit={updateProcessGroupWithMessages}
          hideSubmitButton
          onChange={updateFormData}
          submitButtonText="Save"
          bpmnEvent={messageEvent}
        />
      </>
    );
  }

  return null;
}
