import {
  useEffect,
  useState,
  type ChangeEvent,
  type Dispatch,
  type SetStateAction,
} from 'react';
import { useTranslation } from 'react-i18next';
import { ErrorOutline, FilterAlt as FilterIcon } from '@mui/icons-material';
import {
  Autocomplete,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  Typography,
  Grid,
  IconButton,
  TextField,
} from '@mui/material';

import { Link, useSearchParams } from 'react-router-dom';
import PaginationForTable from '../PaginationForTable';
import ProcessBreadcrumb from '../ProcessBreadcrumb';
import {
  getPageInfoFromSearchParams,
  getProcessStatus,
  getMessageType,
  modifyProcessIdentifierForPathParam,
} from '../../helpers';
import HttpService from '../../services/HttpService';
import { FormatProcessModelDisplayName } from '../MiniComponents';
import { ProcessModel, MessageInstance, MessageModel } from '../../interfaces';
import DateAndTimeService from '../../services/DateAndTimeService';
import SpiffTooltip from '../SpiffTooltip';

import ProcessModelSearch from '../ProcessModelSearch';
import { MESSAGE_STATUSES, MESSAGE_TYPES } from '../../config';

type OwnProps = {
  processInstanceId?: number;
};

const paginationQueryParamPrefix = 'message-list';

export default function MessageInstanceList({ processInstanceId }: OwnProps) {
  const { t } = useTranslation();
  const [messageInstances, setMessageInstances] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [searchParams] = useSearchParams();

  const [messageInstanceForModal, setMessageInstanceForModal] =
    useState<MessageInstance | null>(null);

  const [filtersVisible, setFiltersVisible] = useState<boolean>(false);
  const [processModelAvailableItems, setProcessModelAvailableItems] = useState<
    ProcessModel[]
  >([]);
  const [processModelSelection, setProcessModelSelection] =
    useState<ProcessModel | null>(null);
  const [messageModelAvailableItems, setMessageModelAvailableItems] = useState<
    MessageModel[]
  >([]);
  const [messageModelSelection, setMessageModelSelection] =
    useState<MessageModel | null>(null);
  const [messageTypeOptions, setMessageTypeOptions] = useState<string[]>([]);
  const [messageTypeSelection, setMessageTypeSelection] = useState<string[]>(
    [],
  );
  const [messageStatusOptions, setMessageStatusOptions] = useState<string[]>(
    [],
  );
  const [messageStatusSelection, setMessageStatusSelection] = useState<
    string[]
  >([]);
  const [startDate, setStartDate] = useState<string>('');
  const [startTime, setStartTime] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [endTime, setEndTime] = useState<string>('');
  const [createdAfter, setCreatedAfter] = useState<number | null>(null);
  const [createdBefore, setCreatedBefore] = useState<number | null>(null);

  const updateValidatedInputValue = (
    event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
    setter: Dispatch<SetStateAction<string>>,
  ) => {
    const input = event.target as HTMLInputElement;
    if (input.value === '' || input.validity.valid) {
      setter(input.value);
    }
  };

  useEffect(() => {
    function parseAvailableProcessModels(result: any) {
      const items = result.results.map((item: any) => {
        const label = `${item.id}`;
        Object.assign(item, { label });
        return item;
      });
      setProcessModelAvailableItems(items);
    }

    HttpService.makeCallToBackend({
      path: `/process-models?per_page=1500&recursive=true&include_parent_groups=true`,
      successCallback: parseAvailableProcessModels,
    });

    HttpService.makeCallToBackend({
      path: `/all-message-models`,
      successCallback: (result: any) => {
        const items = result.messages;
        setMessageModelAvailableItems(items);
      },
    });

    setMessageTypeOptions(MESSAGE_TYPES);
    setMessageStatusOptions(MESSAGE_STATUSES);
  }, []);

  useEffect(() => {
    if (startDate == '') {
      setCreatedAfter(null);
    } else if (startDate) {
      const createdAfterInSeconds =
        DateAndTimeService.convertDateAndTimeStringsToSeconds(
          startDate,
          startTime || '00:00:00',
        );
      setCreatedAfter(
        Number.isFinite(createdAfterInSeconds) ? createdAfterInSeconds : null,
      );
    }
  }, [startDate, startTime]);

  useEffect(() => {
    if (endDate == '') {
      setCreatedBefore(null);
    }
    if (endDate) {
      const createdBeforeInSeconds =
        DateAndTimeService.convertDateAndTimeStringsToSeconds(
          endDate,
          endTime || '00:00:00',
        );
      setCreatedBefore(
        Number.isFinite(createdBeforeInSeconds) ? createdBeforeInSeconds : null,
      );
    }
  }, [endDate, endTime]);

  useEffect(() => {
    const setMessageInstanceListFromResult = (result: any) => {
      setMessageInstances(result.results);
      setPagination(result.pagination);
    };
    const { page, perPage } = getPageInfoFromSearchParams(
      searchParams,
      undefined,
      undefined,
      paginationQueryParamPrefix,
    );
    let queryParamString = `per_page=${perPage}&page=${page}`;
    if (processInstanceId) {
      queryParamString += `&process_instance_id=${processInstanceId}`;
    }

    const body = {
      process_model_identifier: processModelSelection
        ? processModelSelection.id
        : null,
      name: messageModelSelection ? messageModelSelection.identifier : null,
      message_type:
        messageTypeSelection.length > 0 ? messageTypeSelection : null,
      status: messageStatusSelection.length > 0 ? messageStatusSelection : null,
      created_after: createdAfter,
      created_before: createdBefore,
    };

    HttpService.makeCallToBackend({
      path: `/messages?${queryParamString}`,
      httpMethod: 'POST',
      postBody: body,
      successCallback: setMessageInstanceListFromResult,
    });
  }, [
    processInstanceId,
    searchParams,
    processModelSelection,
    messageModelSelection,
    messageTypeSelection,
    messageStatusSelection,
    createdAfter,
    createdBefore,
  ]);

  const handleCorrelationDisplayClose = () => {
    setMessageInstanceForModal(null);
  };

  const correlationsDisplayModal = () => {
    if (messageInstanceForModal) {
      let failureCausePre = null;
      if (messageInstanceForModal.failure_cause) {
        failureCausePre = (
          <>
            <Typography variant="body1" className="failure-string">
              {messageInstanceForModal.failure_cause}
            </Typography>
            <br />
          </>
        );
      }
      return (
        <Dialog
          open={!!messageInstanceForModal}
          onClose={handleCorrelationDisplayClose}
          aria-labelledby="dialog-title"
          aria-describedby="dialog-description"
        >
          <DialogTitle id="dialog-title">
            {t('message_title', {
              id: messageInstanceForModal.id,
              name: messageInstanceForModal.name,
              type: messageInstanceForModal.message_type,
            })}
          </DialogTitle>
          <DialogContent>
            {failureCausePre}
            <DialogContentText>{t('correlations')}:</DialogContentText>
            <pre>
              {JSON.stringify(
                messageInstanceForModal.correlation_keys,
                null,
                2,
              )}
            </pre>
          </DialogContent>
        </Dialog>
      );
    }
    return null;
  };

  const showFilters = () => {
    const elements = [];
    elements.push(
      <Grid container justifyContent="flex-end">
        <SpiffTooltip title={t('filter_options')}>
          <IconButton
            data-testid="filter-section-expand-toggle"
            color="primary"
            aria-label={t('filter_options')}
            onClick={() => setFiltersVisible(!filtersVisible)}
          >
            <FilterIcon />
          </IconButton>
        </SpiffTooltip>
      </Grid>,
    );
    if (filtersVisible) {
      elements.push(
        <Grid container className="with-bottom-margin" spacing={1}>
          <Grid size={{ xs: 12, md: 6, lg: 3 }}>
            <ProcessModelSearch
              onChange={(selection: ProcessModel | null) =>
                setProcessModelSelection(selection)
              }
              processModels={processModelAvailableItems}
              selectedItem={processModelSelection}
              truncateProcessModelDisplayName
            />
          </Grid>
          <Grid size={{ xs: 12, md: 6, lg: 3 }}>
            <Autocomplete
              id="message-model-select"
              className="process-model-search-combobox"
              options={messageModelAvailableItems}
              getOptionLabel={(item: MessageModel) =>
                `${item.identifier} (${item.location})`
              }
              value={messageModelSelection}
              onChange={(_event, value) => setMessageModelSelection(value)}
              isOptionEqualToValue={(option, value) =>
                option.identifier === value.identifier &&
                option.location === value.location
              }
              renderInput={(params) => (
                <TextField
                  {...params}
                  label={t('name')}
                  placeholder={t('choose_a_message')}
                />
              )}
            />
          </Grid>
          <Grid size={{ xs: 12, md: 6, lg: 3 }}>
            <Autocomplete
              multiple
              className="message-type-select"
              id="message-instance-type-select"
              options={messageTypeOptions}
              value={messageTypeSelection}
              onChange={(_event, value) => setMessageTypeSelection(value)}
              getOptionLabel={(item: string) => getMessageType(item)}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label={t('type')}
                  placeholder={t('choose_type')}
                />
              )}
            />
          </Grid>
          <Grid size={{ xs: 12, md: 6, lg: 3 }}>
            <Autocomplete
              multiple
              className="message-status-select"
              id="message-instance-status-select"
              options={messageStatusOptions}
              value={messageStatusSelection}
              onChange={(_event, value) => setMessageStatusSelection(value)}
              getOptionLabel={(item: string) => getProcessStatus(item)}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label={t('status')}
                  placeholder={t('choose_status')}
                />
              )}
            />
          </Grid>
        </Grid>,
      );
      elements.push(
        <Grid container className="with-bottom-margin" spacing={1}>
          <Grid size={{ xs: 12, md: 6, lg: 3 }}>
            <TextField
              id="start-date"
              label={`${t('created_after')} ${t('date')}`}
              type="date"
              value={startDate}
              onChange={(event) =>
                updateValidatedInputValue(event, setStartDate)
              }
              slotProps={{ inputLabel: { shrink: true } }}
            />
          </Grid>
          <Grid size={{ xs: 12, md: 6, lg: 3 }}>
            <TextField
              id="start-time-input"
              label={t('time')}
              type="time"
              value={startTime}
              onChange={(event) =>
                updateValidatedInputValue(event, setStartTime)
              }
              slotProps={{
                inputLabel: { shrink: true },
                htmlInput: { step: 60 },
              }}
            />
          </Grid>
          <Grid size={{ xs: 12, md: 6, lg: 3 }}>
            <TextField
              id="end-date"
              label={`${t('created_before')} ${t('date')}`}
              type="date"
              value={endDate}
              onChange={(event) => updateValidatedInputValue(event, setEndDate)}
              slotProps={{ inputLabel: { shrink: true } }}
            />
          </Grid>
          <Grid size={{ xs: 12, md: 6, lg: 3 }}>
            <TextField
              id="end-time-input"
              label={t('time')}
              type="time"
              value={endTime}
              onChange={(event) => updateValidatedInputValue(event, setEndTime)}
              slotProps={{
                inputLabel: { shrink: true },
                htmlInput: { step: 60 },
              }}
            />
          </Grid>
        </Grid>,
      );
    }
    return elements;
  };

  const buildTable = () => {
    const rows = messageInstances.map((row: MessageInstance) => {
      let errorIcon = null;
      let errorTitle = null;
      if (row.failure_cause) {
        errorTitle = t('instance_has_error');
        errorIcon = (
          <>
            &nbsp;
            <ErrorOutline style={{ fill: 'red' }} />
          </>
        );
      }
      let processLink = <span>{t('external_call_label')}</span>;
      let instanceLink = <span />;
      if (row.process_instance_id != null) {
        processLink = FormatProcessModelDisplayName(row);
        instanceLink = (
          <Link
            data-testid="process-instance-show-link"
            to={`/process-instances/${modifyProcessIdentifierForPathParam(
              row.process_model_identifier,
            )}/${row.process_instance_id}`}
          >
            {row.process_instance_id}
          </Link>
        );
      }
      return (
        <TableRow key={row.id}>
          <TableCell>{row.id}</TableCell>
          <TableCell>{processLink}</TableCell>
          <TableCell>{instanceLink}</TableCell>
          <TableCell>{row.name}</TableCell>
          <TableCell>{getMessageType(row.message_type)}</TableCell>
          <TableCell>{row.counterpart_id}</TableCell>
          <TableCell>
            <SpiffTooltip title={errorTitle}>
              <Button
                variant="text"
                onClick={() => setMessageInstanceForModal(row)}
              >
                {t('view')}
                {errorIcon}
              </Button>
            </SpiffTooltip>
          </TableCell>
          <TableCell>{getProcessStatus(row.status)}</TableCell>
          <TableCell>
            {DateAndTimeService.convertSecondsToFormattedDateTime(
              row.created_at_in_seconds,
            )}
          </TableCell>
        </TableRow>
      );
    });
    return (
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>{t('message_id')}</TableCell>
              <TableCell>{t('process_label')}</TableCell>
              <TableCell>{t('process_label_instance')}</TableCell>
              <TableCell>{t('name')}</TableCell>
              <TableCell>{t('type')}</TableCell>
              <TableCell>{t('corresponding_message_instance')}</TableCell>
              <TableCell>{t('details_label')}</TableCell>
              <TableCell>{t('status')}</TableCell>
              <TableCell>{t('created_at_label')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>{rows}</TableBody>
        </Table>
      </TableContainer>
    );
  };

  if (pagination) {
    const { page, perPage } = getPageInfoFromSearchParams(
      searchParams,
      undefined,
      undefined,
      paginationQueryParamPrefix,
    );
    let breadcrumbElement = null;
    if (searchParams.get('process_instance_id')) {
      breadcrumbElement = (
        <ProcessBreadcrumb
          hotCrumbs={[
            [t('process_groups'), '/process-groups'],
            {
              entityToExplode: searchParams.get('process_model_id') || '',
              entityType: 'process-model-id',
              linkLastItem: true,
            },
            [
              `Process Instance: ${searchParams.get('process_instance_id')}`,
              `/process-instances/${searchParams.get(
                'process_model_id',
              )}/${searchParams.get('process_instance_id')}`,
            ],
            [t('messages_tab')],
          ]}
        />
      );
    }
    return (
      <>
        {breadcrumbElement}
        {correlationsDisplayModal()}
        {showFilters()}
        <PaginationForTable
          page={page}
          perPage={perPage}
          perPageOptions={[10, 50, 100, 500, 1000]}
          pagination={pagination}
          tableToDisplay={buildTable()}
          paginationQueryParamPrefix={paginationQueryParamPrefix}
        />
      </>
    );
  }
  return null;
}
