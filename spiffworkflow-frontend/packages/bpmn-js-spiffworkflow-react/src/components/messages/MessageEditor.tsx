import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Alert, Box } from '@mui/material';

import type { BpmnApiService } from '../../services/BpmnApiService';
import {
  areCorrelationPropertiesInSync,
  convertCorrelationPropertiesToFormData,
  mergeCorrelationProperties,
  ProcessGroup,
  MessageDefinition,
} from './MessageHelper';

type MessageEditorFormData = {
  processGroupIdentifier: string;
  messageId: string;
  correlation_properties?: Array<{ id: string; retrievalExpression?: string }>;
  schema?: string;
};

type MessageEditorFormProps = {
  formData: MessageEditorFormData;
  schema: Record<string, unknown>;
  uiSchema: Record<string, unknown>;
  onSubmit: (formData: MessageEditorFormData) => void;
  onChange: (formData: MessageEditorFormData) => void;
};

type MessageEditorProps = {
  apiService: Pick<BpmnApiService, 'getProcessGroup' | 'updateProcessGroup'>;
  processGroupIdentifier: string;
  messageId: string;
  messageEvent: any;
  correlationProperties: Array<{ id: string; retrievalExpression?: string }>;
  elementId: string;
  renderForm: (props: MessageEditorFormProps) => React.ReactNode;
};

const unModifyProcessIdentifierForPathParam = (path: string) => {
  return path.replace(/:/g, '/') || '';
};

export default function MessageEditor({
  apiService,
  processGroupIdentifier,
  messageId,
  messageEvent,
  correlationProperties,
  elementId,
  renderForm,
}: MessageEditorProps) {
  const [processGroup, setProcessGroup] = useState<ProcessGroup | null>(null);
  const [currentFormData, setCurrentFormData] =
    useState<MessageEditorFormData | null>(null);
  const [displaySaveMessage, setDisplaySaveMessage] = useState(false);
  const [displayNotSyncedMessage, setDisplayNotSyncedMessage] = useState(false);
  const [currentMessageId, setCurrentMessageId] = useState<string | null>(null);
  const [schemaError, setSchemaError] = useState<string | null>(null);

  const updateCorrelationPropertiesOnProcessGroup = useCallback(
    (currentMessagesForId: MessageDefinition, formData: MessageEditorFormData) => {
      const newCorrelationProperties = {
        ...(currentMessagesForId.correlation_properties || {}),
      };
      (formData.correlation_properties || []).forEach((formProp) => {
        newCorrelationProperties[formProp.id] = {
          retrieval_expression: formProp.retrievalExpression || '',
        };
      });
      Object.keys(currentMessagesForId.correlation_properties || {}).forEach(
        (propId: string) => {
          const foundProp = (formData.correlation_properties || []).find(
            (formProp) => propId === formProp.id,
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
    (response: ProcessGroup, messageIdentifier: string, updatedMessagesForId: MessageDefinition) => {
      setProcessGroup(response);
      setDisplaySaveMessage(true);
      setDisplayNotSyncedMessage(false);
      if (messageEvent?.eventBus) {
        messageEvent.eventBus.fire('spiff.add_message.returned', {
          name: messageIdentifier,
          correlation_properties: updatedMessagesForId.correlation_properties,
          elementId,
        });
      }
    },
    [elementId, messageEvent],
  );

  const updateProcessGroupWithMessages = useCallback(
    async (formData: MessageEditorFormData) => {
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
      const updatedMessagesForId = { ...currentMessagesForId };

      const newCorrelationProperties =
        updateCorrelationPropertiesOnProcessGroup(currentMessagesForId, formData);

      updatedMessagesForId.correlation_properties = newCorrelationProperties;

      try {
        updatedMessagesForId.schema = JSON.parse(formData.schema || '{}');
      } catch (error) {
        setSchemaError(
          error instanceof Error ? error.message : 'Invalid JSON schema',
        );
        return;
      }

      if (oldMessageId !== newMessageId) {
        delete processGroupForUpdate.messages[oldMessageId];
      }

      processGroupForUpdate.messages[newMessageId] = updatedMessagesForId;
      setCurrentMessageId(newMessageId);
      setSchemaError(null);

      if (!apiService.updateProcessGroup) {
        setSchemaError('Message editor API is not configured');
        return;
      }

      const response = await apiService.updateProcessGroup(
        processGroupIdentifier,
        processGroupForUpdate,
      );
      if (response) {
        handleProcessGroupUpdateResponse(
          response,
          newMessageId,
          updatedMessagesForId,
        );
      }
    },
    [
      apiService,
      currentMessageId,
      handleProcessGroupUpdateResponse,
      processGroup,
      processGroupIdentifier,
      updateCorrelationPropertiesOnProcessGroup,
    ],
  );

  useEffect(() => {
    const setInitialFormData = (newProcessGroup: ProcessGroup) => {
      let newCorrelationProperties = convertCorrelationPropertiesToFormData(
        messageId,
        newProcessGroup,
      );
      newCorrelationProperties = mergeCorrelationProperties(
        correlationProperties,
        newCorrelationProperties,
      );
      const jsonSchema =
        (newProcessGroup.messages || {})[messageId]?.schema || {};
      const newFormData: MessageEditorFormData = {
        processGroupIdentifier: unModifyProcessIdentifierForPathParam(
          processGroupIdentifier,
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
      setInitialFormData(result);
    };

    if (!apiService.getProcessGroup) {
      setSchemaError('Message editor API is not configured');
      return;
    }

    apiService
      .getProcessGroup(processGroupIdentifier)
      .then((result) => {
        if (result) {
          processResult(result);
        }
      })
      .catch((error) => {
        setSchemaError(
          error instanceof Error ? error.message : 'Failed to load process group',
        );
      });
  }, [apiService, correlationProperties, messageId, processGroupIdentifier]);

  const schema = useMemo(
    () => ({
      type: 'object',
      required: ['processGroupIdentifier', 'messageId'],
      properties: {
        processGroupIdentifier: {
          type: 'string',
          title: 'Location',
          default: '/',
          pattern: '^[\\/\\w-]+$',
        },
        messageId: {
          type: 'string',
          title: 'Message Name',
          pattern: '^[\\w-]+$',
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
              },
              retrievalExpression: {
                type: 'string',
                title: 'Retrieval Expression',
              },
            },
          },
        },
        schema: {
          type: 'string',
          title: 'Message Schema (JSON)',
        },
      },
    }),
    [],
  );

  const uiSchema = useMemo(
    () => ({
      processGroupIdentifier: {
        'ui:readonly': true,
      },
      schema: {
        'ui:widget': 'textarea',
        'ui:options': {
          rows: 8,
        },
      },
      correlation_properties: {
        items: {
          retrievalExpression: {
            'ui:placeholder': 'payload.foo',
          },
        },
      },
    }),
    [],
  );

  if (!currentFormData) {
    return null;
  }

  return (
    <Box>
      {displaySaveMessage ? (
        <Alert severity="success" sx={{ mb: 2 }}>
          Message has been saved
        </Alert>
      ) : null}
      {displayNotSyncedMessage && !displaySaveMessage ? (
        <Alert severity="warning" sx={{ mb: 2 }}>
          Message definition is not synced with the diagram
        </Alert>
      ) : null}
      {schemaError ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {schemaError}
        </Alert>
      ) : null}
      {renderForm({
        formData: currentFormData,
        schema,
        uiSchema,
        onSubmit: updateProcessGroupWithMessages,
        onChange: (formData) => {
          setCurrentFormData(formData);
          setDisplaySaveMessage(false);
        },
      })}
    </Box>
  );
}
