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
  modifyProcessIdentifierForPathParam,
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

type SavedMessageData = {
  messageId: string;
  location: string;
  correlationProperties: Array<{
    id: string;
    retrievalExpression?: string;
  }>;
};

type OwnProps = {
  modifiedProcessGroupIdentifier: string;
  elementId: string;
  messageId: string;
  messageEvent: any;
  correlationProperties: any;
  hideSubmitButton?: boolean;
  onSave?: (savedMessage: SavedMessageData) => void;
  managePageTitle?: boolean;
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
  hideSubmitButton = true,
  onSave,
  managePageTitle = true,
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
  const [currentMessageLocation, setCurrentMessageLocation] = useState<
    string | null
  >(null);
  const [currentSharedMessageModelId, setCurrentSharedMessageModelId] =
    useState<number | null>(null);
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
      messageLocation: string,
    ) => {
      setProcessGroup(response);
      setCurrentMessageLocation(messageLocation);
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

  const saveProcessGroupAtLocation = useCallback(
    (
      location: string,
      processGroupToUpdate: ProcessGroup,
      successCallback: (response: ProcessGroup) => void,
      failureCallback?: () => void,
    ) => {
      HttpService.makeCallToBackend({
        path: `/process-groups/${modifyProcessIdentifierForPathParam(location)}`,
        successCallback,
        failureCallback,
        httpMethod: 'PUT',
        postBody: processGroupToUpdate,
      });
    },
    [],
  );

  const updateProcessGroupWithMessages = useCallback(
    (formObject: RJSFFormObject) => {
      const { formData } = formObject as { formData: MessageEditorFormData };

      if (!processGroup) {
        return;
      }

      const newMessageId = formData.messageId;
      const oldMessageId = currentMessageId || newMessageId;
      const sourceLocation = currentMessageLocation || currentGroupLocation;
      const targetLocation =
        formData.processGroupIdentifier || currentGroupLocation;

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
        selectedSharedMessageOption.message.location === targetLocation &&
        selectedSharedMessageOption.message.location !== sourceLocation;

      const persistedMessageDefinition: MessageDefinition = {
        ...updatedMessagesForId,
      };
      const persistedMessageModelId =
        currentSharedMessageModelId || selectedSharedMessageOption?.id || null;
      if (sourceLocation !== targetLocation) {
        persistedMessageDefinition.id = persistedMessageModelId || undefined;
        persistedMessageDefinition.location = targetLocation;
      } else {
        delete persistedMessageDefinition.id;
        delete persistedMessageDefinition.location;
      }

      const updateComplete = (response: ProcessGroup) => {
        setCurrentMessageId(newMessageId);
        setCurrentSharedMessageModelId(persistedMessageModelId);
        setCurrentFormData({
          ...formData,
          processGroupIdentifier: targetLocation,
        });
        handleProcessGroupUpdateResponse(
          response,
          newMessageId,
          updatedMessagesForId,
          targetLocation,
        );
        onSave?.({
          messageId: newMessageId,
          location: targetLocation,
          correlationProperties: Object.entries(newCorrelationProperties).map(
            ([id, correlationProperty]) => ({
              id,
              retrievalExpression: correlationProperty.retrieval_expression,
            }),
          ),
        });
      };

      if (shouldInheritAncestorSharedMessage) {
        delete processGroupForUpdate.messages[newMessageId];
        if (oldMessageId !== newMessageId) {
          delete processGroupForUpdate.messages[oldMessageId];
        }
        saveProcessGroupAtLocation(
          sourceLocation,
          processGroupForUpdate,
          (response) => {
            setCurrentSharedMessageModelId(
              selectedSharedMessageOption.message.id,
            );
            updateComplete(response);
          },
        );
        return;
      }

      if (sourceLocation === targetLocation) {
        processGroupForUpdate.messages[newMessageId] =
          persistedMessageDefinition;
        if (oldMessageId !== newMessageId) {
          delete processGroupForUpdate.messages[oldMessageId];
        }
        saveProcessGroupAtLocation(
          sourceLocation,
          processGroupForUpdate,
          updateComplete,
        );
        return;
      }
      HttpService.makeCallToBackend({
        path: `/process-groups/${modifyProcessIdentifierForPathParam(sourceLocation)}/messages/${encodeURIComponent(
          oldMessageId,
        )}/move`,
        successCallback: updateComplete,
        httpMethod: 'PUT',
        postBody: {
          target_process_group_identifier: targetLocation,
          target_message_identifier: newMessageId,
          message_definition: persistedMessageDefinition,
        },
      });
    },
    [
      currentGroupLocation,
      currentMessageId,
      currentMessageLocation,
      currentSharedMessageModelId,
      handleProcessGroupUpdateResponse,
      processGroup,
      saveProcessGroupAtLocation,
      sharedMessageOptionsById,
      updateCorrelationPropertiesOnProcessGroup,
      t,
      onSave,
    ],
  );

  useEffect(() => {
    const setInitialFormData = (
      newProcessGroup: ProcessGroup,
      matchingMessageModels: MessageModelResponse[],
    ) => {
      const currentProcessGroupMessage = (newProcessGroup.messages || {})[
        messageId
      ];
      const currentMessageDefinitionLocation =
        currentProcessGroupMessage?.location || currentGroupLocation;
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
        currentProcessGroupMessage?.schema || {};
      const jsonSchemaFromSelectedSharedMessage =
        nearestMessageModel?.schema || {};
      const newFormData: MessageEditorFormData = {
        processGroupIdentifier:
          (currentMessageDefinitionLocation ?? nearestMessageModel?.location) ||
          currentGroupLocation,
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
      setCurrentMessageLocation(currentMessageDefinitionLocation);
      setCurrentSharedMessageModelId(
        nearestMessageModel?.location === currentMessageDefinitionLocation
          ? nearestMessageModel.id
          : null,
      );
    };

    const processResult = (
      processGroupResult: ProcessGroup,
      messageModelsResult: { messages: MessageModelResponse[] },
    ) => {
      const matchingMessageModels = (messageModelsResult.messages || []).filter(
        (messageModel) => {
          return messageModel.identifier === messageId;
        },
      );
      const newIsSynced = areCorrelationPropertiesInSync(
        processGroupResult,
        messageId,
        correlationProperties,
        currentGroupLocation,
        matchingMessageModels,
      );
      setDisplayNotSyncedMessage(!newIsSynced);
      setProcessGroup(processGroupResult);
      setCurrentMessageId(messageId);
      setCurrentMessageLocation(
        matchingMessageModels[0]?.location || currentGroupLocation,
      );
      if (managePageTitle) {
        setPageTitle([processGroupResult.display_name]);
      }
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
  }, [
    modifiedProcessGroupIdentifier,
    correlationProperties,
    currentGroupLocation,
    managePageTitle,
    messageId,
  ]);

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
    if (!currentFormData) {
      setCurrentFormData(nextFormData);
      return;
    }

    const sharedMessageOption =
      selectedSharedMessageId === NO_SHARED_MESSAGE_OPTION
        ? null
        : sharedMessageOptionsById[selectedSharedMessageId || ''];
    if (!sharedMessageOption) {
      const deselectedInheritedSharedMessage =
        currentFormData.useExistingSharedMessageId !==
          NO_SHARED_MESSAGE_OPTION &&
        currentFormData.processGroupIdentifier !== currentGroupLocation;
      if (deselectedInheritedSharedMessage) {
        setCurrentSharedMessageModelId(null);
        setCurrentFormData({
          ...nextFormData,
          processGroupIdentifier: currentGroupLocation,
        });
        return;
      }

      setCurrentFormData(nextFormData);
      return;
    }

    const sharedMessageSelectionChanged =
      selectedSharedMessageId !== currentFormData.useExistingSharedMessageId;
    if (!sharedMessageSelectionChanged) {
      const inheritedSharedMessageWasCustomized =
        sharedMessageOption.message.location !== currentGroupLocation &&
        (nextFormData.messageId !== currentFormData.messageId ||
          nextFormData.processGroupIdentifier !==
            currentFormData.processGroupIdentifier ||
          nextFormData.schema !== currentFormData.schema ||
          JSON.stringify(nextFormData.correlation_properties || []) !==
            JSON.stringify(currentFormData.correlation_properties || []));

      if (inheritedSharedMessageWasCustomized) {
        setCurrentSharedMessageModelId(null);
        setCurrentFormData({
          ...nextFormData,
          processGroupIdentifier:
            nextFormData.processGroupIdentifier ===
            sharedMessageOption.message.location
              ? currentGroupLocation
              : nextFormData.processGroupIdentifier,
          useExistingSharedMessageId: NO_SHARED_MESSAGE_OPTION,
        });
        return;
      }

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
          hideSubmitButton={hideSubmitButton}
          onChange={updateFormData}
          submitButtonText={t('save')}
          bpmnEvent={messageEvent}
        />
      </>
    );
  }

  return null;
}
