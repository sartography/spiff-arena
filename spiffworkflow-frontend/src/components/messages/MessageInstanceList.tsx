import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ErrorOutline, FilterAlt as FilterIcon } from '@mui/icons-material';
import {
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
} from '@mui/material';
import {
  ComboBox,
  MultiSelect,
  DatePicker,
  DatePickerInput,
  TimePicker,
} from '@carbon/react';

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

import ProcessModelSearchCarbon from '../ProcessModelSearchCarbon';
import {
  MESSAGE_STATUSES,
  MESSAGE_TYPES,
  DATE_FORMAT_CARBON,
  DATE_FORMAT_FOR_DISPLAY,
} from '../../config';

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
    any[]
  >([]);
  const [messageModelSelection, setMessageModelSelection] = useState<
    any | null
  >(null);
  const [messageTypeOptions, setMessageTypeOptions] = useState<string[]>([]);
  const [messageTypeSelection, setMessageTypeSelection] = useState<any | null>(
    null,
  );
  const [messageStatusOptions, setMessageStatusOptions] = useState<string[]>(
    [],
  );
  const [messageStatusSelection, setMessageStatusSelection] = useState<
    string[]
  >([]);
  const [startDate, setStartDate] = useState<string>('');
  const [startTime, setStartTime] = useState<string>('');
  const [startTimeInvalid, setStartTimeInvalid] = useState<boolean>(false);
  const [endDate, setEndDate] = useState<string>('');
  const [endTime, setEndTime] = useState<string>('');
  const [endTimeInvalid, setEndTimeInvalid] = useState<boolean>(false);
  const [createdAfter, setCreatedAfter] = useState<string | null>(null);
  const [createdBefore, setCreatedBefore] = useState<string | null>(null);

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
      path: `/message-models-list`,
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
    } else if (startDate && !startTimeInvalid) {
      setCreatedAfter(
        DateAndTimeService.convertDateAndTimeStringsToSeconds(
          startDate,
          startTime || '00:00:00',
        ),
      );
    }
  }, [startDate, startTime, startTimeInvalid]);

  useEffect(() => {
    if (endDate == '') {
      setCreatedBefore(null);
    }
    if (endDate && !endTimeInvalid) {
      setCreatedBefore(
        DateAndTimeService.convertDateAndTimeStringsToSeconds(
          endDate,
          endTime || '00:00:00',
        ),
      );
    }
  }, [endDate, endTime, endTimeInvalid]);

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
      message_type: messageTypeSelection || null,
      status: messageStatusSelection || null,
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
      <Grid container fullWidth justifyContent="flex-end">
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
        <Grid container fullWidth className="with-bottom-margin" spacing={1}>
          <Grid>
            <ProcessModelSearchCarbon
              onChange={(selection: any) =>
                setProcessModelSelection(selection.selectedItem)
              }
              processModels={processModelAvailableItems}
              selectedItem={processModelSelection}
              truncateProcessModelDisplayName
            />
          </Grid>
          <Grid>
            <ComboBox
              id="message-model-select"
              className="process-model-search-combobox"
              titleText={t('name')}
              placeHolder={t('choose_a_message')}
              items={messageModelAvailableItems}
              itemToString={(item: MessageModel) => {
                if (item) {
                  return `${item.identifier} (${item.location})`;
                }
              }}
              selectedItem={messageModelSelection}
              onChange={(selection: any) =>
                setMessageModelSelection(selection.selectedItem)
              }
            />
          </Grid>
          <Grid>
            <MultiSelect
              label={t('choose_type')}
              className="message-type-select"
              id="message-instance-type-select"
              titleText={t('type')}
              items={messageTypeOptions}
              onChange={(selection: any) =>
                setMessageTypeSelection(selection.selectedItems)
              }
              itemToString={(item: any) => getMessageType(item)}
              selectionFeedback="top-after-reopen"
              selectedItems={messageTypeSelection}
            />
          </Grid>
          <Grid>
            <MultiSelect
              label={t('choose_status')}
              className="message-status-select"
              id="message-instance-status-select"
              titleText={t('status')}
              items={messageStatusOptions}
              onChange={(selection: any) =>
                setMessageStatusSelection(selection.selectedItems)
              }
              itemToString={(item: any) => getProcessStatus(item)}
              selectionFeedback="top-after-reopen"
              selectedItems={messageStatusSelection}
            />
          </Grid>
        </Grid>,
      );
      elements.push(
        <Grid container fullWidth className="with-bottom-margin" spacing={1}>
          <Grid>
            <DatePicker
              id="start-date"
              datePickerType="single"
              dateFormat={DATE_FORMAT_CARBON}
              value={startDate}
            >
              <DatePickerInput
                id="start-date-input"
                labelText={`${t('created_after')} ${t('date')}`}
                type="text"
                size="md"
                autocomplete="off"
                allowInput={false}
                placeHolder={DATE_FORMAT_FOR_DISPLAY}
                onChange={(ev: any) => setStartDate(ev.target.value)}
              />
            </DatePicker>
          </Grid>
          <Grid>
            <TimePicker
              id="start-time-input"
              labelText={t('time')}
              pattern="^([01]\d|2[0-3]):?([0-5]\d)$"
              value={startTime}
              invalid={startTimeInvalid}
              onChange={(ev: any) => {
                setStartTimeInvalid(!ev.target.validity.valid);
                setStartTime(ev.target.value);
              }}
            />
          </Grid>
          <Grid>
            <DatePicker
              id="end-date"
              datePickerType="single"
              dateFormat={DATE_FORMAT_CARBON}
              value={endDate}
            >
              <DatePickerInput
                id="end-date-input"
                labelText={`${t('created_before')} ${t('date')}`}
                type="text"
                size="md"
                autocomplete="off"
                allowInput={false}
                placeHolder={DATE_FORMAT_FOR_DISPLAY}
                onChange={(ev: any) => setEndDate(ev.target.value)}
              />
            </DatePicker>
          </Grid>
          <Grid>
            <TimePicker
              id="end-time-input"
              labelText={t('time')}
              value={endTime}
              invalid={endTimeInvalid}
              onChange={(ev: any) => {
                setEndTimeInvalid(!ev.target.validity.valid);
                setEndTime(ev.target.value);
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
