import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
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
  const [displayNotSyncedMessage, setDisplayNotSyncedMessage] =
    useState<boolean>(false);
  const [currentMessageId, setCurrentMessageId] = useState<string | null>(null);
  const { t } = useTranslation();

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
      setDisplayNotSyncedMessage(false);
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
        alert(t('invalid_schema_error', { error: e }));
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
      t,
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
      setDisplayNotSyncedMessage(!newIsSynced);
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
        title: t('location'),
        default: '/',
        pattern: '^[\\/\\w-]+$',
        validationErrorMessage: t('location_validation_error'),
        description: t('location_description'),
      },
      messageId: {
        type: 'string',
        title: t('message_name'),
        pattern: '^[\\w-]+$',
        validationErrorMessage: t('message_name_validation_error'),
        description: t('message_name_description'),
      },
      correlation_properties: {
        type: 'array',
        title: t('correlation_properties'),
        items: {
          type: 'object',
          required: ['id', 'retrievalExpression'],
          properties: {
            id: {
              type: 'string',
              title: t('property_name'),
              description: t('property_name_description'),
              pattern: '^[\\w-]+$',
              validationErrorMessage: t('property_name_validation_error'),
            },
            retrievalExpression: {
              type: 'string',
              title: t('retrieval_expression'),
              description: t('retrieval_expression_description'),
            },
          },
        },
      },
      schema: {
        type: 'string',
        title: t('json_schema'),
        default: '{}',
        description: t('json_schema_description_editor'),
      },
    },
  };

  const uischema = {
    schema: {
      'ui:widget': 'textarea',
      'ui:rows': 5,
      'ui:options': { validateJson: true },
    },
    'ui:order': [
      'processGroupIdentifier',
      'messageId',
      'schema',
      'correlation_properties',
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
            title={t('save_success_title')}
            hideCloseButton
            timeout={4000}
            onClose={() => setDisplaySaveMessageMessage(false)}
          >
            {t('save_success_message')}
          </Notification>
        ) : null}
        {displayNotSyncedMessage && !displaySaveMessageMessage ? (
          <Notification
            title={t('save_warning_title')}
            type="warning"
            hideCloseButton
            timeout={4000}
            onClose={() => setDisplayNotSyncedMessage(false)}
          >
            {t('save_warning_message')}
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
          submitButtonText={t('save')}
          bpmnEvent={messageEvent}
        />
      </>
    );
  }

  return null;
}
