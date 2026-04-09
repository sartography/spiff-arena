import React, { useEffect, useMemo, useState } from 'react';
import {
  Box,
  Button,
  Dialog,
  DialogContent,
  DialogTitle,
  Link,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import { useSearchParams } from 'react-router-dom';
import HttpService from '../../services/HttpService';
import {
  getPageInfoFromSearchParams,
  modifyProcessIdentifierForPathParam,
} from '../../helpers';
import { PaginationObject } from '../../interfaces';
import PaginationForTable from '../PaginationForTable';
import { MessageEditor } from './MessageEditor';
import { findNearestAncestorLocation } from './MessageHelper';

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
        matches.find((messageModel) => messageModel.location === nearestLocation) ||
        null
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
  const [selectedMessageModel, setSelectedMessageModel] =
    useState<MessageModelResponse | null>(null);
  const [searchParams] = useSearchParams();
  const { t } = useTranslation();
  const { page, perPage } = getPageInfoFromSearchParams(
    searchParams,
    undefined,
    undefined,
    paginationQueryParamPrefix,
  );

  useEffect(() => {
    const path = processGroupId
      ? `/message-models/${modifyProcessIdentifierForPathParam(
          processGroupId,
        )}`
      : '/all-message-models';

    HttpService.makeCallToBackend({
      path,
      successCallback: (result: { messages: MessageModelResponse[] }) => {
        const messages = result.messages || [];
        setMessageModels(messages);
        setSelectedMessageModel(
          getInitialSelectedMessageModel(
            messages,
            initialMessageId,
            initialSourceLocation,
          ),
        );
      },
    });
  }, [processGroupId, initialMessageId, initialSourceLocation]);

  const paginatedMessageModels = useMemo(() => {
    const startingIndex = (page - 1) * perPage;
    return messageModels.slice(startingIndex, startingIndex + perPage);
  }, [messageModels, page, perPage]);

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
            <Button onClick={() => setSelectedMessageModel(messageModel)}>
              {t('edit')}
            </Button>
          </TableCell>
        </TableRow>
      );
    });
  }, [paginatedMessageModels, t]);

  const table = (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>{t('id')}</TableCell>
            <TableCell>{t('location')}</TableCell>
            <TableCell>{t('correlations')}</TableCell>
            <TableCell>{t('used_in')}</TableCell>
            <TableCell align="right">{t('edit')}</TableCell>
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
        open={selectedMessageModel != null}
        onClose={() => setSelectedMessageModel(null)}
        fullWidth
        maxWidth="md"
      >
        {selectedMessageModel ? (
          <>
            <DialogTitle>
              {`${selectedMessageModel.identifier} (${selectedMessageModel.location})`}
            </DialogTitle>
            <DialogContent>
              <Box sx={{ pt: 1 }}>
                <MessageEditor
                  modifiedProcessGroupIdentifier={modifyProcessIdentifierForPathParam(selectedMessageModel.location)}
                  messageId={selectedMessageModel.identifier}
                  messageEvent={noOpBpmnEvent}
                  correlationProperties={selectedMessageModel.correlation_properties.map(
                    (correlationProperty) => ({
                      id: correlationProperty.identifier,
                      retrievalExpression:
                        correlationProperty.retrieval_expression,
                    }),
                  )}
                  elementId={`${selectedMessageModel.location}:${selectedMessageModel.identifier}`}
                />
              </Box>
            </DialogContent>
          </>
        ) : null}
      </Dialog>
    </>
  );
}
