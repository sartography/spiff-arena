import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Link,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import { useSearchParams } from 'react-router-dom';
import HttpService from '../../services/HttpService';
import { Notification } from '../Notification';
import {
  getPageInfoFromSearchParams,
  modifyProcessIdentifierForPathParam,
} from '../../helpers';
import { PaginationObject, ProcessGroup } from '../../interfaces';
import PaginationForTable from '../PaginationForTable';
import { MessageEditor } from './MessageEditor';
import { findNearestAncestorLocation } from './MessageHelper';
import ConfirmButton from '../ConfirmButton';

type OwnProps = {
  processGroupId?: string;
  initialMessageId?: string;
  initialSourceLocation?: string;
};

type MessageModelResponse = {
  id: number;
  identifier: string;
  location: string;
  schema: any;
  correlation_properties: Array<{
    identifier: string;
    retrieval_expression: string;
  }>;
  process_model_identifiers: string[];
};

type EditorState = {
  messageId: string;
  location: string;
  correlationProperties: Array<{
    id: string;
    retrievalExpression?: string;
  }>;
};

const noOpBpmnEvent = {
  eventBus: {
    fire: () => {},
    on: () => {},
    off: () => {},
    once: () => {},
  },
};

const correlationSummary = (messageModel: MessageModelResponse): string => {
  return messageModel.correlation_properties
    .map((property) => property.identifier)
    .join(', ');
};

const paginationQueryParamPrefix = 'message-model-list';

const toEditorState = (messageModel: MessageModelResponse): EditorState => {
  return {
    messageId: messageModel.identifier,
    location: messageModel.location,
    correlationProperties: messageModel.correlation_properties.map(
      (correlationProperty) => ({
        id: correlationProperty.identifier,
        retrievalExpression: correlationProperty.retrieval_expression,
      }),
    ),
  };
};

const getInitialSelectedMessageModel = (
  messages: MessageModelResponse[],
  initialMessageId?: string,
  initialSourceLocation?: string,
) => {
  if (!initialMessageId) {
    return null;
  }

  const matches = messages.filter((messageModel) => {
    return messageModel.identifier === initialMessageId;
  });
  if (matches.length === 0) {
    return null;
  }

  if (initialSourceLocation) {
    const nearestLocation = findNearestAncestorLocation(
      initialSourceLocation,
      matches.map((messageModel) => messageModel.location),
    );
    if (nearestLocation) {
      return (
        matches.find(
          (messageModel) => messageModel.location === nearestLocation,
        ) || null
      );
    }
  }

  return matches.length === 1 ? matches[0] : null;
};

export default function MessageModelList({
  processGroupId,
  initialMessageId,
  initialSourceLocation,
}: OwnProps) {
  const [messageModels, setMessageModels] = useState<MessageModelResponse[]>(
    [],
  );
  const [editorState, setEditorState] = useState<EditorState | null>(null);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [createLocation, setCreateLocation] = useState(processGroupId || '');
  const [createLocationError, setCreateLocationError] = useState('');
  const [isValidatingCreateLocation, setIsValidatingCreateLocation] =
    useState(false);
  const [deletedMessageNotification, setDeletedMessageNotification] = useState<{
    identifier: string;
    location: string;
  } | null>(null);
  const hasInitializedEditor = useRef(false);
  const [searchParams, setSearchParams] = useSearchParams();
  const { t } = useTranslation();
  const { page, perPage } = getPageInfoFromSearchParams(
    searchParams,
    undefined,
    undefined,
    paginationQueryParamPrefix,
  );

  const listPath = processGroupId
    ? `/message-models/${modifyProcessIdentifierForPathParam(processGroupId)}`
    : '/all-message-models';

  const loadMessageModels = useCallback(
    (selectedMessage?: { identifier: string; location: string } | null) => {
      HttpService.makeCallToBackend({
        path: listPath,
        successCallback: (result: { messages: MessageModelResponse[] }) => {
          const messages = result.messages || [];
          setMessageModels(messages);

          if (selectedMessage === null) {
            setEditorState(null);
            return;
          }

          if (selectedMessage) {
            const matchingMessageModel = messages.find((messageModel) => {
              return (
                messageModel.identifier === selectedMessage.identifier &&
                messageModel.location === selectedMessage.location
              );
            });
            if (matchingMessageModel) {
              setEditorState(toEditorState(matchingMessageModel));
            }
            return;
          }

          if (!hasInitializedEditor.current) {
            hasInitializedEditor.current = true;
            const initialMessageModel = getInitialSelectedMessageModel(
              messages,
              initialMessageId,
              initialSourceLocation,
            );
            if (initialMessageModel) {
              setEditorState(toEditorState(initialMessageModel));
            }
          }
        },
      });
    },
    [initialMessageId, initialSourceLocation, listPath],
  );

  useEffect(() => {
    hasInitializedEditor.current = false;
    setEditorState(null);
    setCreateLocation(processGroupId || '');
    setCreateLocationError('');
    setIsCreateDialogOpen(false);
    const path = processGroupId
      ? `/message-models/${modifyProcessIdentifierForPathParam(processGroupId)}`
      : '/all-message-models';
    if (path === listPath) {
      loadMessageModels();
    }
  }, [loadMessageModels, listPath, processGroupId]);

  const paginatedMessageModels = useMemo(() => {
    const startingIndex = (page - 1) * perPage;
    return messageModels.slice(startingIndex, startingIndex + perPage);
  }, [messageModels, page, perPage]);

  const openCreateDialog = useCallback(() => {
    setCreateLocation(processGroupId || '');
    setCreateLocationError('');
    setIsCreateDialogOpen(true);
  }, [processGroupId]);

  const closeCreateDialog = useCallback(() => {
    setCreateLocationError('');
    setIsValidatingCreateLocation(false);
    setIsCreateDialogOpen(false);
  }, []);

  const validateCreateLocation = useCallback(() => {
    const normalizedLocation = createLocation.trim();
    if (!normalizedLocation) {
      setCreateLocationError(t('location_required'));
      return;
    }

    setCreateLocationError('');
    setIsValidatingCreateLocation(true);
    HttpService.makeCallToBackend({
      path: `/process-groups/${modifyProcessIdentifierForPathParam(
        normalizedLocation,
      )}`,
      successCallback: () => {
        setIsValidatingCreateLocation(false);
        setIsCreateDialogOpen(false);
        setEditorState({
          messageId: '',
          location: normalizedLocation,
          correlationProperties: [],
        });
      },
      failureCallback: () => {
        setIsValidatingCreateLocation(false);
        setCreateLocationError(t('message_model_location_not_found'));
      },
    });
  }, [createLocation, t]);

  const closeEditor = useCallback(() => {
    setEditorState(null);
    // Clear message_id and source_location params when closing editor
    const nextSearchParams = new URLSearchParams(searchParams);
    nextSearchParams.delete('message_id');
    nextSearchParams.delete('source_location');
    setSearchParams(nextSearchParams, { replace: true });
  }, [searchParams, setSearchParams]);

  const deleteMessageModel = useCallback(
    (messageModel: MessageModelResponse) => {
      const modifiedLocation = modifyProcessIdentifierForPathParam(
        messageModel.location,
      );
      HttpService.makeCallToBackend({
        path: `/process-groups/${modifiedLocation}`,
        successCallback: (processGroup: ProcessGroup) => {
          const updatedMessages = {
            ...(processGroup.messages || {}),
          };
          delete updatedMessages[messageModel.identifier];

          const updatedProcessGroup: ProcessGroup = {
            ...processGroup,
            messages: updatedMessages,
          };

          HttpService.makeCallToBackend({
            path: `/process-groups/${modifiedLocation}`,
            successCallback: () => {
              setDeletedMessageNotification({
                identifier: messageModel.identifier,
                location: messageModel.location,
              });
              loadMessageModels(null);
            },
            httpMethod: 'PUT',
            postBody: updatedProcessGroup,
          });
        },
      });
    },
    [loadMessageModels],
  );

  const rows = useMemo(() => {
    return paginatedMessageModels.map((messageModel) => {
      const usedIn = (messageModel.process_model_identifiers || []).map(
        (pmId) => (
          <Link
            key={pmId}
            href={`/process-models/${modifyProcessIdentifierForPathParam(pmId)}`}
            underline="hover"
            sx={{ display: 'block', whiteSpace: 'nowrap' }}
          >
            {pmId}
          </Link>
        ),
      );
      return (
        <TableRow
          key={`${messageModel.location}:${messageModel.identifier}`}
          hover
        >
          <TableCell>{messageModel.identifier}</TableCell>
          <TableCell>
            <Link
              href={`/process-groups/${modifyProcessIdentifierForPathParam(
                messageModel.location,
              )}`}
              underline="hover"
            >
              {messageModel.location}
            </Link>
          </TableCell>
          <TableCell>{correlationSummary(messageModel)}</TableCell>
          <TableCell>{usedIn.length > 0 ? usedIn : null}</TableCell>
          <TableCell align="right">
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
              <Button
                onClick={() => setEditorState(toEditorState(messageModel))}
              >
                {t('edit')}
              </Button>
              <ConfirmButton
                buttonLabel={t('delete')}
                onConfirmation={() => deleteMessageModel(messageModel)}
                title={t('delete_message_model_confirmation')}
                description={
                  (messageModel.process_model_identifiers || []).length > 0
                    ? t('delete_message_model_description_used_in', {
                        identifier: messageModel.identifier,
                        location: messageModel.location,
                        usedIn: (
                          messageModel.process_model_identifiers || []
                        ).join(', '),
                      })
                    : t('delete_message_model_description', {
                        identifier: messageModel.identifier,
                        location: messageModel.location,
                      })
                }
                confirmButtonLabel={t('delete')}
                variant="text"
                color="error"
              />
            </Box>
          </TableCell>
        </TableRow>
      );
    });
  }, [deleteMessageModel, paginatedMessageModels, t]);

  const table = (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>{t('id')}</TableCell>
            <TableCell>{t('location')}</TableCell>
            <TableCell>{t('correlations')}</TableCell>
            <TableCell>{t('used_in')}</TableCell>
            <TableCell align="right">{t('actions')}</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.length > 0 ? (
            rows
          ) : (
            <TableRow>
              <TableCell colSpan={5}>
                <Typography variant="body2">{t('no_results')}</Typography>
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </TableContainer>
  );

  const pagination: PaginationObject | null =
    messageModels.length > 0
      ? {
          count: paginatedMessageModels.length,
          total: messageModels.length,
          pages: Math.ceil(messageModels.length / perPage),
        }
      : null;

  return (
    <>
      {deletedMessageNotification ? (
        <Notification
          title={t('delete_message_model_success_title')}
          hideCloseButton
          timeout={4000}
          onClose={() => setDeletedMessageNotification(null)}
        >
          {t('delete_message_model_success_message', {
            identifier: deletedMessageNotification.identifier,
            location: deletedMessageNotification.location,
          })}
        </Notification>
      ) : null}
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
        <Button variant="contained" onClick={openCreateDialog}>
          {t('add_message_model')}
        </Button>
      </Box>
      {pagination ? (
        <PaginationForTable
          page={page}
          perPage={perPage}
          pagination={pagination}
          tableToDisplay={table}
          paginationQueryParamPrefix={paginationQueryParamPrefix}
        />
      ) : (
        table
      )}
      <Dialog
        open={editorState != null}
        onClose={closeEditor}
        fullWidth
        maxWidth="md"
      >
        {editorState ? (
          <>
            <DialogTitle>
              {editorState.messageId
                ? `${editorState.messageId} (${editorState.location})`
                : t('new_message_model_title', {
                    location: editorState.location,
                  })}
            </DialogTitle>
            <DialogContent>
              <Box sx={{ pt: 1 }}>
                <MessageEditor
                  modifiedProcessGroupIdentifier={modifyProcessIdentifierForPathParam(
                    editorState.location,
                  )}
                  messageId={editorState.messageId}
                  messageEvent={noOpBpmnEvent}
                  correlationProperties={editorState.correlationProperties}
                  elementId={`${editorState.location}:${editorState.messageId || 'new-message-model'}`}
                  hideSubmitButton={true}
                  managePageTitle={false}
                  onSave={(savedMessage) => {
                    setEditorState(savedMessage);
                    loadMessageModels({
                      identifier: savedMessage.messageId,
                      location: savedMessage.location,
                    });
                  }}
                />
              </Box>
            </DialogContent>
            <DialogActions>
              <Button
                variant="contained"
                color="primary"
                onClick={() => {
                  const submitButton = document.getElementById('submit-button');
                  if (submitButton) {
                    (submitButton as HTMLButtonElement).click();
                  }
                }}
              >
                {t('save')}
              </Button>
              <Button onClick={closeEditor}>{t('close')}</Button>
            </DialogActions>
          </>
        ) : null}
      </Dialog>
      <Dialog
        open={isCreateDialogOpen}
        onClose={closeCreateDialog}
        fullWidth
        maxWidth="sm"
      >
        <DialogTitle>{t('choose_message_model_location')}</DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ mb: 2 }}>
            {t('choose_message_model_location_description')}
          </DialogContentText>
          <TextField
            autoFocus
            fullWidth
            label={t('location')}
            value={createLocation}
            error={Boolean(createLocationError)}
            helperText={createLocationError || ' '}
            onChange={(event) => {
              setCreateLocation(event.target.value);
              if (createLocationError) {
                setCreateLocationError('');
              }
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={closeCreateDialog}>{t('cancel')}</Button>
          <Button
            variant="contained"
            onClick={validateCreateLocation}
            disabled={isValidatingCreateLocation}
          >
            {t('continue')}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
