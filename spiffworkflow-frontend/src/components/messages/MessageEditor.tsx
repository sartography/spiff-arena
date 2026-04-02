import { useCallback, useEffect, useMemo, useState } from 'react';
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
  findNearestAncestorLocation,
} from './MessageHelper';
import { Notification } from '../Notification';

type MessageModelResponse = {
  id: number;
  identifier: string;
  location: string;
  schema: any;
  correlation_properties: Array<{
    identifier: string;
    retrieval_expression: string;
  }>;
};

type SharedMessageOption = {
  id: number;
  label: string;
  message: MessageModelResponse;
};

type MessageEditorFormData = {
  processGroupIdentifier: string;
  messageId: string;
  useExistingSharedMessageId?: string;
  correlation_properties?: Array<{
    id: string;
    retrievalExpression?: string;
  }>;
  schema?: string;
};

type OwnProps = {
  modifiedProcessGroupIdentifier: string;
  elementId: string;
  messageId: string;
  messageEvent: any;
  correlationProperties: any;
};

const NO_SHARED_MESSAGE_OPTION = 'none';

const toCorrelationProperties = (
  correlationProperties: MessageModelResponse['correlation_properties'] = [],
) => {
  return correlationProperties.map((correlationProperty) => ({
    id: correlationProperty.identifier,
    retrievalExpression: correlationProperty.retrieval_expression,
  }));
};

export function MessageEditor({
  modifiedProcessGroupIdentifier,
  messageId,
  messageEvent,
  correlationProperties,
  elementId,
}: OwnProps) {
  const currentGroupLocation = unModifyProcessIdentifierForPathParam(
    modifiedProcessGroupIdentifier,
  );
  const [processGroup, setProcessGroup] = useState<ProcessGroup | null>(null);
  const [currentFormData, setCurrentFormData] =
    useState<MessageEditorFormData | null>(null);
  const [displaySaveMessageMessage, setDisplaySaveMessageMessage] =
    useState<boolean>(false);
  const [displayNotSyncedMessage, setDisplayNotSyncedMessage] =
    useState<boolean>(false);
  const [currentMessageId, setCurrentMessageId] = useState<string | null>(null);
  const [sharedMessageOptions, setSharedMessageOptions] = useState<
    SharedMessageOption[]
  >([]);
  const { t } = useTranslation();

  const sharedMessageOptionsById = useMemo(() => {
    const byId: Record<string, SharedMessageOption> = {};
    sharedMessageOptions.forEach((sharedMessageOption) => {
      byId[String(sharedMessageOption.id)] = sharedMessageOption;
    });
    return byId;
  }, [sharedMessageOptions]);

  const updateCorrelationPropertiesOnProcessGroup = useCallback(
    (
      currentMessagesForId: MessageDefinition,
      formData: MessageEditorFormData,
    ) => {
      const newCorrelationProperties: CorrelationProperties = {
        ...(currentMessagesForId.correlation_properties || {}),
      };
      (formData.correlation_properties || []).forEach((formProp: any) => {
        newCorrelationProperties[formProp.id] = {
          retrieval_expression: formProp.retrievalExpression,
        };
      });
      Object.keys(currentMessagesForId.correlation_properties || {}).forEach(
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
      const { formData } = formObject as { formData: MessageEditorFormData };

      if (!processGroup) {
        return;
      }

      const newMessageId = formData.messageId;
      const oldMessageId = currentMessageId || newMessageId;

      const processGroupForUpdate = { ...processGroup };
      if (!processGroupForUpdate.messages) {
        processGroupForUpdate.messages = {};
      }
      const currentMessagesForId: MessageDefinition =
        (processGroupForUpdate.messages || {})[oldMessageId] || {};
      const updatedMessagesForId: MessageDefinition = {
        ...currentMessagesForId,
      };

      const newCorrelationProperties =
        updateCorrelationPropertiesOnProcessGroup(
          currentMessagesForId,
          formData,
        );

      updatedMessagesForId.correlation_properties = newCorrelationProperties;

      try {
        updatedMessagesForId.schema = JSON.parse(formData.schema || '{}');
      } catch (e) {
        alert(t('invalid_schema_error', { error: e }));
        return;
      }

      const selectedSharedMessageOption =
        sharedMessageOptionsById[formData.useExistingSharedMessageId || ''];
      const shouldInheritAncestorSharedMessage =
        selectedSharedMessageOption != null &&
        selectedSharedMessageOption.message.location !== currentGroupLocation;

      if (shouldInheritAncestorSharedMessage) {
        delete processGroupForUpdate.messages[newMessageId];
      } else {
        delete updatedMessagesForId.id;
        delete updatedMessagesForId.location;
        processGroupForUpdate.messages[newMessageId] = updatedMessagesForId;
      }
      if (oldMessageId !== newMessageId) {
        delete processGroupForUpdate.messages[oldMessageId];
      }
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
      currentGroupLocation,
      sharedMessageOptionsById,
      updateCorrelationPropertiesOnProcessGroup,
      t,
    ],
  );

  useEffect(() => {
    const setInitialFormData = (
      newProcessGroup: ProcessGroup,
      matchingMessageModels: MessageModelResponse[],
    ) => {
      const candidateLocations = matchingMessageModels.map((messageModel) => {
        return messageModel.location;
      });
      const nearestLocation = findNearestAncestorLocation(
        currentGroupLocation,
        candidateLocations,
      );
      const nearestMessageModel = matchingMessageModels.find((messageModel) => {
        return messageModel.location === nearestLocation;
      });

      const newSharedMessageOptions: SharedMessageOption[] =
        matchingMessageModels.map((messageModel) => {
          return {
            id: messageModel.id,
            label: `${messageModel.identifier} (${messageModel.location})`,
            message: messageModel,
          };
        });
      setSharedMessageOptions(newSharedMessageOptions);

      const correlationPropertiesFromProcessGroup =
        convertCorrelationPropertiesToRJSF(messageId, newProcessGroup);
      const correlationPropertiesFromSelectedSharedMessage = nearestMessageModel
        ? toCorrelationProperties(nearestMessageModel.correlation_properties)
        : [];
      let newCorrelationProperties = mergeCorrelationProperties(
        correlationProperties,
        correlationPropertiesFromProcessGroup,
      );
      newCorrelationProperties = mergeCorrelationProperties(
        newCorrelationProperties,
        correlationPropertiesFromSelectedSharedMessage,
      );

      const jsonSchemaFromProcessGroup =
        (newProcessGroup.messages || {})[messageId]?.schema || {};
      const jsonSchemaFromSelectedSharedMessage =
        nearestMessageModel?.schema || {};
      const newFormData: MessageEditorFormData = {
        processGroupIdentifier:
          nearestMessageModel?.location || currentGroupLocation,
        messageId,
        useExistingSharedMessageId: nearestMessageModel
          ? String(nearestMessageModel.id)
          : NO_SHARED_MESSAGE_OPTION,
        correlation_properties: newCorrelationProperties,
        schema: JSON.stringify(
          Object.keys(jsonSchemaFromSelectedSharedMessage || {}).length > 0
            ? jsonSchemaFromSelectedSharedMessage
            : jsonSchemaFromProcessGroup,
          null,
          2,
        ),
      };
      setCurrentFormData(newFormData);
    };

    const processResult = (
      processGroupResult: ProcessGroup,
      messageModelsResult: { messages: MessageModelResponse[] },
    ) => {
      const newIsSynced = areCorrelationPropertiesInSync(
        processGroupResult,
        messageId,
        correlationProperties,
      );
      setDisplayNotSyncedMessage(!newIsSynced);
      setProcessGroup(processGroupResult);
      setCurrentMessageId(messageId);
      setPageTitle([processGroupResult.display_name]);

      const matchingMessageModels = (messageModelsResult.messages || []).filter(
        (messageModel) => {
          return messageModel.identifier === messageId;
        },
      );
      setInitialFormData(processGroupResult, matchingMessageModels);
    };

    let processGroupResult: ProcessGroup | null = null;
    let processGroupLoaded = false;
    let messageModelsResult: { messages: MessageModelResponse[] } = {
      messages: [],
    };
    let messageModelsLoaded = false;

    const maybeFinalize = () => {
      if (processGroupLoaded && messageModelsLoaded && processGroupResult) {
        processResult(processGroupResult, messageModelsResult);
      }
    };

    HttpService.makeCallToBackend({
      path: `/process-groups/${modifiedProcessGroupIdentifier}`,
      successCallback: (result: ProcessGroup) => {
        processGroupResult = result;
        processGroupLoaded = true;
        maybeFinalize();
      },
    });

    HttpService.makeCallToBackend({
      path: `/message-models/${modifiedProcessGroupIdentifier}`,
      successCallback: (result: { messages: MessageModelResponse[] }) => {
        messageModelsResult = result;
        messageModelsLoaded = true;
        maybeFinalize();
      },
      failureCallback: () => {
        messageModelsResult = { messages: [] };
        messageModelsLoaded = true;
        maybeFinalize();
      },
    });
  }, [modifiedProcessGroupIdentifier, correlationProperties, messageId]);

  const schema = useMemo(() => {
    return {
      type: 'object',
      required: ['processGroupIdentifier', 'messageId'],
      properties: {
        useExistingSharedMessageId: {
          type: 'string',
          title: t('use_existing_shared_message'),
          oneOf: [
            {
              const: NO_SHARED_MESSAGE_OPTION,
              title: t('do_not_use_existing_shared_message'),
            },
            ...sharedMessageOptions.map((sharedMessageOption) => ({
              const: String(sharedMessageOption.id),
              title: sharedMessageOption.label,
            })),
          ],
          description: t('use_existing_shared_message_description'),
        },
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
  }, [sharedMessageOptions, t]);

  const uischema = {
    schema: {
      'ui:widget': 'textarea',
      'ui:rows': 5,
      'ui:options': { validateJson: true },
    },
    'ui:order': [
      'useExistingSharedMessageId',
      'processGroupIdentifier',
      'messageId',
      'schema',
      'correlation_properties',
    ],
  };

  const updateFormData = (formObject: any) => {
    const nextFormData = formObject.formData as MessageEditorFormData;
    const selectedSharedMessageId = nextFormData.useExistingSharedMessageId;
    const sharedMessageOption =
      selectedSharedMessageId === NO_SHARED_MESSAGE_OPTION
        ? null
        : sharedMessageOptionsById[selectedSharedMessageId || ''];

    if (!sharedMessageOption || !currentFormData) {
      setCurrentFormData(nextFormData);
      return;
    }

    const sharedMessageSelectionChanged =
      selectedSharedMessageId !== currentFormData.useExistingSharedMessageId;
    if (!sharedMessageSelectionChanged) {
      setCurrentFormData(nextFormData);
      return;
    }

    const nextCorrelationProperties = mergeCorrelationProperties(
      nextFormData.correlation_properties || [],
      toCorrelationProperties(
        sharedMessageOption.message.correlation_properties,
      ),
    );

    setCurrentFormData({
      ...nextFormData,
      processGroupIdentifier: sharedMessageOption.message.location,
      correlation_properties: nextCorrelationProperties,
      schema: JSON.stringify(sharedMessageOption.message.schema || {}, null, 2),
    });
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
