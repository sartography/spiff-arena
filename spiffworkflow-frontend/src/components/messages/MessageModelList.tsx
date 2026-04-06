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
import HttpService from '../../services/HttpService';
import { modifyProcessIdentifierForPathParam } from '../../helpers';
import { MessageEditor } from './MessageEditor';

type OwnProps = {
  processGroupId?: string;
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
};

const noOpBpmnEvent = {
  eventBus: {
    fire: () => {},
  },
};

const correlationSummary = (messageModel: MessageModelResponse): string => {
  return messageModel.correlation_properties
    .map((property) => property.identifier)
    .join(', ');
};

export default function MessageModelList({ processGroupId }: OwnProps) {
  const [messageModels, setMessageModels] = useState<MessageModelResponse[]>(
    [],
  );
  const [selectedMessageModel, setSelectedMessageModel] =
    useState<MessageModelResponse | null>(null);
  const { t } = useTranslation();

  useEffect(() => {
    const queryParamString = 'per_page=100&page=1';
    const path = processGroupId
      ? `/message-models/${modifyProcessIdentifierForPathParam(
          processGroupId,
        )}?${queryParamString}`
      : `/all-message-models?${queryParamString}`;

    HttpService.makeCallToBackend({
      path,
      successCallback: (result: { messages: MessageModelResponse[] }) => {
        setMessageModels(result.messages || []);
      },
    });
  }, [processGroupId]);

  const rows = useMemo(() => {
    return messageModels.map((messageModel) => {
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
          <TableCell align="right">
            <Button onClick={() => setSelectedMessageModel(messageModel)}>
              {t('edit')}
            </Button>
          </TableCell>
        </TableRow>
      );
    });
  }, [messageModels, t]);

  return (
    <>
      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>{t('id')}</TableCell>
              <TableCell>{t('location')}</TableCell>
              <TableCell>{t('correlations')}</TableCell>
              <TableCell align="right">{t('edit')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.length > 0 ? (
              rows
            ) : (
              <TableRow>
                <TableCell colSpan={4}>
                  <Typography variant="body2">{t('no_results')}</Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
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
                  modifiedProcessGroupIdentifier={selectedMessageModel.location}
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
