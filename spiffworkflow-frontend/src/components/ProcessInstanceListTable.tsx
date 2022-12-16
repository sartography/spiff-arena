import { useContext, useEffect, useMemo, useState } from 'react';
import {
  Link,
  useNavigate,
  useParams,
  useSearchParams,
} from 'react-router-dom';

// @ts-ignore
import { Filter, Close, AddAlt } from '@carbon/icons-react';
import {
  Button,
  ButtonSet,
  DatePicker,
  DatePickerInput,
  Table,
  Grid,
  Column,
  MultiSelect,
  TableHeader,
  TableHead,
  TableRow,
  TimePicker,
  Tag,
  Stack,
  Modal,
  ComboBox,
  TextInput,
  FormLabel,
  // @ts-ignore
} from '@carbon/react';
import { PROCESS_STATUSES, DATE_FORMAT, DATE_FORMAT_CARBON } from '../config';
import {
  convertDateAndTimeStringsToSeconds,
  convertDateObjectToFormattedHoursMinutes,
  convertSecondsToFormattedDateString,
  convertSecondsToFormattedDateTime,
  convertSecondsToFormattedTimeHoursMinutes,
  getPageInfoFromSearchParams,
  getProcessModelFullIdentifierFromSearchParams,
  modifyProcessIdentifierForPathParam,
  refreshAtInterval,
} from '../helpers';

import PaginationForTable from './PaginationForTable';
import 'react-datepicker/dist/react-datepicker.css';

import ErrorContext from '../contexts/ErrorContext';
import HttpService from '../services/HttpService';

import 'react-bootstrap-typeahead/css/Typeahead.css';
import 'react-bootstrap-typeahead/css/Typeahead.bs5.css';
import {
  PaginationObject,
  ProcessModel,
  ProcessInstanceReport,
  ProcessInstance,
  ReportColumn,
  ReportColumnForEditing,
  ReportMetadata,
  ReportFilter,
} from '../interfaces';
import ProcessModelSearch from './ProcessModelSearch';
import ProcessInstanceReportSearch from './ProcessInstanceReportSearch';
import ProcessInstanceListSaveAsReport from './ProcessInstanceListSaveAsReport';
import { FormatProcessModelDisplayName } from './MiniComponents';
import { Notification } from './Notification';

const REFRESH_INTERVAL = 5;
const REFRESH_TIMEOUT = 600;

type OwnProps = {
  filtersEnabled?: boolean;
  processModelFullIdentifier?: string;
  paginationQueryParamPrefix?: string;
  perPageOptions?: number[];
  showReports?: boolean;
  reportIdentifier?: string;
  textToShowIfEmpty?: string;
  paginationClassName?: string;
  autoReload?: boolean;
  additionalParams?: string;
};

interface dateParameters {
  [key: string]: ((..._args: any[]) => any)[];
}

export default function ProcessInstanceListTable({
  filtersEnabled = true,
  processModelFullIdentifier,
  paginationQueryParamPrefix,
  perPageOptions,
  additionalParams,
  showReports = true,
  reportIdentifier,
  textToShowIfEmpty,
  paginationClassName,
  autoReload = false,
}: OwnProps) {
  const params = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [processInstances, setProcessInstances] = useState([]);
  const [reportMetadata, setReportMetadata] = useState<ReportMetadata | null>();
  const [pagination, setPagination] = useState<PaginationObject | null>(null);
  const [processInstanceFilters, setProcessInstanceFilters] = useState({});

  const oneHourInSeconds = 3600;
  const oneMonthInSeconds = oneHourInSeconds * 24 * 30;
  const [startFromDate, setStartFromDate] = useState<string>('');
  const [startToDate, setStartToDate] = useState<string>('');
  const [endFromDate, setEndFromDate] = useState<string>('');
  const [endToDate, setEndToDate] = useState<string>('');
  const [startFromTime, setStartFromTime] = useState<string>('');
  const [startToTime, setStartToTime] = useState<string>('');
  const [endFromTime, setEndFromTime] = useState<string>('');
  const [endToTime, setEndToTime] = useState<string>('');
  const [showFilterOptions, setShowFilterOptions] = useState<boolean>(false);
  const [startFromTimeInvalid, setStartFromTimeInvalid] =
    useState<boolean>(false);
  const [startToTimeInvalid, setStartToTimeInvalid] = useState<boolean>(false);
  const [endFromTimeInvalid, setEndFromTimeInvalid] = useState<boolean>(false);
  const [endToTimeInvalid, setEndToTimeInvalid] = useState<boolean>(false);

  const setErrorMessage = (useContext as any)(ErrorContext)[1];

  const [processStatusAllOptions, setProcessStatusAllOptions] = useState<any[]>(
    []
  );
  const [processStatusSelection, setProcessStatusSelection] = useState<
    string[]
  >([]);
  const [processModelAvailableItems, setProcessModelAvailableItems] = useState<
    ProcessModel[]
  >([]);
  const [processModelSelection, setProcessModelSelection] =
    useState<ProcessModel | null>(null);
  const [processInstanceReportSelection, setProcessInstanceReportSelection] =
    useState<ProcessInstanceReport | null>(null);

  const [availableReportColumns, setAvailableReportColumns] = useState<
    ReportColumn[]
  >([]);
  const [processInstanceReportJustSaved, setProcessInstanceReportJustSaved] =
    useState<string | null>(null);
  const [showReportColumnForm, setShowReportColumnForm] =
    useState<boolean>(false);
  const [reportColumnToOperateOn, setReportColumnToOperateOn] =
    useState<ReportColumnForEditing | null>(null);
  const [reportColumnFormMode, setReportColumnFormMode] = useState<string>('');

  const dateParametersToAlwaysFilterBy: dateParameters = useMemo(() => {
    return {
      start_from: [setStartFromDate, setStartFromTime],
      start_to: [setStartToDate, setStartToTime],
      end_from: [setEndFromDate, setEndFromTime],
      end_to: [setEndToDate, setEndToTime],
    };
  }, [
    setStartFromDate,
    setStartFromTime,
    setStartToDate,
    setStartToTime,
    setEndFromDate,
    setEndFromTime,
    setEndToDate,
    setEndToTime,
  ]);

  const parametersToGetFromSearchParams = useMemo(() => {
    return {
      process_model_identifier: null,
      process_status: null,
    };
  }, []);

  // eslint-disable-next-line sonarjs/cognitive-complexity
  useEffect(() => {
    function setProcessInstancesFromResult(result: any) {
      const processInstancesFromApi = result.results;
      setProcessInstances(processInstancesFromApi);
      setPagination(result.pagination);
      setProcessInstanceFilters(result.filters);

      setReportMetadata(result.report.report_metadata);
      if (result.report.id) {
        setProcessInstanceReportSelection(result.report);
      }
    }
    function getProcessInstances() {
      // eslint-disable-next-line prefer-const
      let { page, perPage } = getPageInfoFromSearchParams(
        searchParams,
        undefined,
        undefined,
        paginationQueryParamPrefix
      );
      if (perPageOptions && !perPageOptions.includes(perPage)) {
        // eslint-disable-next-line prefer-destructuring
        perPage = perPageOptions[1];
      }
      let queryParamString = `per_page=${perPage}&page=${page}`;

      const userAppliedFilter = searchParams.get('user_filter');
      if (userAppliedFilter) {
        queryParamString += `&user_filter=${userAppliedFilter}`;
      }

      if (searchParams.get('report_id')) {
        queryParamString += `&report_id=${searchParams.get('report_id')}`;
      } else if (reportIdentifier) {
        queryParamString += `&report_identifier=${reportIdentifier}`;
      }

      Object.keys(dateParametersToAlwaysFilterBy).forEach(
        (paramName: string) => {
          const dateFunctionToCall =
            dateParametersToAlwaysFilterBy[paramName][0];
          const timeFunctionToCall =
            dateParametersToAlwaysFilterBy[paramName][1];
          const searchParamValue = searchParams.get(paramName);
          if (searchParamValue) {
            queryParamString += `&${paramName}=${searchParamValue}`;
            const dateString = convertSecondsToFormattedDateString(
              searchParamValue as any
            );
            dateFunctionToCall(dateString);
            const timeString = convertSecondsToFormattedTimeHoursMinutes(
              searchParamValue as any
            );
            timeFunctionToCall(timeString);
            setShowFilterOptions(true);
          }
        }
      );

      Object.keys(parametersToGetFromSearchParams).forEach(
        (paramName: string) => {
          if (
            paramName === 'process_model_identifier' &&
            processModelFullIdentifier
          ) {
            queryParamString += `&process_model_identifier=${processModelFullIdentifier}`;
          } else if (searchParams.get(paramName)) {
            // @ts-expect-error TS(7053) FIXME:
            const functionToCall = parametersToGetFromSearchParams[paramName];
            queryParamString += `&${paramName}=${searchParams.get(paramName)}`;
            if (functionToCall !== null) {
              functionToCall(searchParams.get(paramName) || '');
            }
            setShowFilterOptions(true);
          }
        }
      );

      if (additionalParams) {
        queryParamString += `&${additionalParams}`;
      }

      HttpService.makeCallToBackend({
        path: `/process-instances?${queryParamString}`,
        successCallback: setProcessInstancesFromResult,
      });
    }
    function processResultForProcessModels(result: any) {
      const processModelFullIdentifierFromSearchParams =
        getProcessModelFullIdentifierFromSearchParams(searchParams);
      const selectionArray = result.results.map((item: any) => {
        const label = `${item.id}`;
        Object.assign(item, { label });
        if (label === processModelFullIdentifierFromSearchParams) {
          setProcessModelSelection(item);
        }
        return item;
      });
      setProcessModelAvailableItems(selectionArray);

      const processStatusSelectedArray: string[] = [];
      const processStatusAllOptionsArray = PROCESS_STATUSES.map(
        (processStatusOption: any) => {
          const regex = new RegExp(`\\b${processStatusOption}\\b`);
          if ((searchParams.get('process_status') || '').match(regex)) {
            processStatusSelectedArray.push(processStatusOption);
          }
          return processStatusOption;
        }
      );
      setProcessStatusSelection(processStatusSelectedArray);
      setProcessStatusAllOptions(processStatusAllOptionsArray);

      getProcessInstances();
    }
    const checkFiltersAndRun = () => {
      if (filtersEnabled) {
        // populate process model selection
        HttpService.makeCallToBackend({
          path: `/process-models?per_page=1000&recursive=true`,
          successCallback: processResultForProcessModels,
        });
      } else {
        getProcessInstances();
      }
    };

    checkFiltersAndRun();
    if (autoReload) {
      return refreshAtInterval(
        REFRESH_INTERVAL,
        REFRESH_TIMEOUT,
        checkFiltersAndRun
      );
    }
    return undefined;
  }, [
    autoReload,
    searchParams,
    params,
    oneMonthInSeconds,
    oneHourInSeconds,
    dateParametersToAlwaysFilterBy,
    parametersToGetFromSearchParams,
    filtersEnabled,
    paginationQueryParamPrefix,
    processModelFullIdentifier,
    perPageOptions,
    reportIdentifier,
    additionalParams,
  ]);

  // This sets the filter data using the saved reports returned from the initial instance_list query.
  // This could probably be merged into the main useEffect but it works here now.
  useEffect(() => {
    const filters = processInstanceFilters as any;
    Object.keys(dateParametersToAlwaysFilterBy).forEach((paramName: string) => {
      const dateFunctionToCall = dateParametersToAlwaysFilterBy[paramName][0];
      const timeFunctionToCall = dateParametersToAlwaysFilterBy[paramName][1];
      const paramValue = filters[paramName];
      dateFunctionToCall('');
      timeFunctionToCall('');
      if (paramValue) {
        const dateString = convertSecondsToFormattedDateString(
          paramValue as any
        );
        dateFunctionToCall(dateString);
        const timeString = convertSecondsToFormattedTimeHoursMinutes(
          paramValue as any
        );
        timeFunctionToCall(timeString);
        setShowFilterOptions(true);
      }
    });

    setProcessModelSelection(null);
    processModelAvailableItems.forEach((item: any) => {
      if (item.id === filters.process_model_identifier) {
        setProcessModelSelection(item);
      }
    });

    const processStatusSelectedArray: string[] = [];
    if (filters.process_status) {
      PROCESS_STATUSES.forEach((processStatusOption: any) => {
        const regex = new RegExp(`\\b${processStatusOption}\\b`);
        if (filters.process_status.match(regex)) {
          processStatusSelectedArray.push(processStatusOption);
        }
      });
      setShowFilterOptions(true);
    }
    setProcessStatusSelection(processStatusSelectedArray);
  }, [
    processInstanceFilters,
    dateParametersToAlwaysFilterBy,
    parametersToGetFromSearchParams,
    processModelAvailableItems,
  ]);

  const processInstanceReportSaveTag = () => {
    if (processInstanceReportJustSaved) {
      let titleOperation = 'Updated';
      if (processInstanceReportJustSaved === 'new') {
        titleOperation = 'Created';
      }
      return (
        <Notification
          title={`Perspective: ${titleOperation}`}
          onClose={() => setProcessInstanceReportJustSaved(null)}
        >
          <span>{`'${
            processInstanceReportSelection
              ? processInstanceReportSelection.identifier
              : ''
          }'`}</span>
        </Notification>
      );
    }
    return null;
  };

  // does the comparison, but also returns false if either argument
  // is not truthy and therefore not comparable.
  const isTrueComparison = (param1: any, operation: any, param2: any) => {
    if (param1 && param2) {
      switch (operation) {
        case '<':
          return param1 < param2;
        case '>':
          return param1 > param2;
        default:
          return false;
      }
    } else {
      return false;
    }
  };

  // TODO: after factoring this out page hangs when invalid date ranges and applying the filter
  const calculateStartAndEndSeconds = () => {
    const startFromSeconds = convertDateAndTimeStringsToSeconds(
      startFromDate,
      startFromTime || '00:00:00'
    );
    const startToSeconds = convertDateAndTimeStringsToSeconds(
      startToDate,
      startToTime || '00:00:00'
    );
    const endFromSeconds = convertDateAndTimeStringsToSeconds(
      endFromDate,
      endFromTime || '00:00:00'
    );
    const endToSeconds = convertDateAndTimeStringsToSeconds(
      endToDate,
      endToTime || '00:00:00'
    );
    let valid = true;
    if (isTrueComparison(startFromSeconds, '>', startToSeconds)) {
      setErrorMessage({
        message: '"Start date from" cannot be after "start date to"',
      });
      valid = false;
    }
    if (isTrueComparison(endFromSeconds, '>', endToSeconds)) {
      setErrorMessage({
        message: '"End date from" cannot be after "end date to"',
      });
      valid = false;
    }
    if (isTrueComparison(startFromSeconds, '>', endFromSeconds)) {
      setErrorMessage({
        message: '"Start date from" cannot be after "end date from"',
      });
      valid = false;
    }
    if (isTrueComparison(startToSeconds, '>', endToSeconds)) {
      setErrorMessage({
        message: '"Start date to" cannot be after "end date to"',
      });
      valid = false;
    }

    return {
      valid,
      startFromSeconds,
      startToSeconds,
      endFromSeconds,
      endToSeconds,
    };
  };

  const applyFilter = (event: any) => {
    event.preventDefault();
    const { page, perPage } = getPageInfoFromSearchParams(
      searchParams,
      undefined,
      undefined,
      paginationQueryParamPrefix
    );
    let queryParamString = `per_page=${perPage}&page=${page}&user_filter=true`;
    const {
      valid,
      startFromSeconds,
      startToSeconds,
      endFromSeconds,
      endToSeconds,
    } = calculateStartAndEndSeconds();

    if (!valid) {
      return;
    }

    if (startFromSeconds) {
      queryParamString += `&start_from=${startFromSeconds}`;
    }
    if (startToSeconds) {
      queryParamString += `&start_to=${startToSeconds}`;
    }
    if (endFromSeconds) {
      queryParamString += `&end_from=${endFromSeconds}`;
    }
    if (endToSeconds) {
      queryParamString += `&end_to=${endToSeconds}`;
    }
    if (processStatusSelection.length > 0) {
      queryParamString += `&process_status=${processStatusSelection}`;
    }

    if (processModelSelection) {
      queryParamString += `&process_model_identifier=${processModelSelection.id}`;
    }

    if (processInstanceReportSelection) {
      queryParamString += `&report_id=${processInstanceReportSelection.id}`;
    }

    setErrorMessage(null);
    setProcessInstanceReportJustSaved(null);
    navigate(`/admin/process-instances?${queryParamString}`);
  };

  const dateComponent = (
    labelString: any,
    name: any,
    initialDate: any,
    initialTime: string,
    onChangeDateFunction: any,
    onChangeTimeFunction: any,
    timeInvalid: boolean,
    setTimeInvalid: any
  ) => {
    return (
      <>
        <DatePicker dateFormat={DATE_FORMAT_CARBON} datePickerType="single">
          <DatePickerInput
            id={`date-picker-${name}`}
            placeholder={DATE_FORMAT}
            labelText={labelString}
            type="text"
            size="md"
            autocomplete="off"
            allowInput={false}
            onChange={(dateChangeEvent: any) => {
              if (!initialDate && !initialTime) {
                onChangeTimeFunction(
                  convertDateObjectToFormattedHoursMinutes(new Date())
                );
              }
              onChangeDateFunction(dateChangeEvent.srcElement.value);
            }}
            value={initialDate}
          />
        </DatePicker>
        <TimePicker
          invalid={timeInvalid}
          id="time-picker"
          labelText="Select a time"
          pattern="^([01]\d|2[0-3]):?([0-5]\d)$"
          value={initialTime}
          onChange={(event: any) => {
            if (event.srcElement.validity.valid) {
              setTimeInvalid(false);
            } else {
              setTimeInvalid(true);
            }
            onChangeTimeFunction(event.srcElement.value);
          }}
        />
      </>
    );
  };

  const processStatusSearch = () => {
    return (
      <MultiSelect
        label="Choose Status"
        className="our-class"
        id="process-instance-status-select"
        titleText="Status"
        items={processStatusAllOptions}
        onChange={(selection: any) => {
          setProcessStatusSelection(selection.selectedItems);
        }}
        itemToString={(item: any) => {
          return item || '';
        }}
        selectionFeedback="top-after-reopen"
        selectedItems={processStatusSelection}
      />
    );
  };

  const clearFilters = () => {
    setProcessModelSelection(null);
    setProcessStatusSelection([]);
    setStartFromDate('');
    setStartFromTime('');
    setStartToDate('');
    setStartToTime('');
    setEndFromDate('');
    setEndFromTime('');
    setEndToDate('');
    setEndToTime('');
  };

  const processInstanceReportDidChange = (selection: any, mode?: string) => {
    clearFilters();
    const selectedReport = selection.selectedItem;
    setProcessInstanceReportSelection(selectedReport);

    let queryParamString = '';
    if (selectedReport) {
      queryParamString = `?report_id=${selectedReport.id}`;
    }

    setErrorMessage(null);
    setProcessInstanceReportJustSaved(mode || null);
    navigate(`/admin/process-instances${queryParamString}`);
  };

  const reportColumns = () => {
    return (reportMetadata as any).columns;
  };

  const reportColumnAccessors = () => {
    return reportColumns().map((reportColumn: ReportColumn) => {
      return reportColumn.accessor;
    });
  };

  // TODO onSuccess reload/select the new report in the report search
  const onSaveReportSuccess = (result: any, mode: string) => {
    processInstanceReportDidChange(
      {
        selectedItem: result,
      },
      mode
    );
  };

  const saveAsReportComponent = () => {
    const {
      valid,
      startFromSeconds,
      startToSeconds,
      endFromSeconds,
      endToSeconds,
    } = calculateStartAndEndSeconds();

    if (!valid || !reportMetadata) {
      return null;
    }
    return (
      <ProcessInstanceListSaveAsReport
        onSuccess={onSaveReportSuccess}
        buttonClassName="button-white-background narrow-button"
        columnArray={reportColumns()}
        orderBy=""
        buttonText="Save"
        processModelSelection={processModelSelection}
        processStatusSelection={processStatusSelection}
        processInstanceReportSelection={processInstanceReportSelection}
        reportMetadata={reportMetadata}
        startFromSeconds={startFromSeconds}
        startToSeconds={startToSeconds}
        endFromSeconds={endFromSeconds}
        endToSeconds={endToSeconds}
      />
    );
  };

  const removeColumn = (reportColumn: ReportColumn) => {
    if (reportMetadata) {
      const reportMetadataCopy = { ...reportMetadata };
      const newColumns = reportColumns().filter(
        (rc: ReportColumn) => rc.accessor !== reportColumn.accessor
      );
      Object.assign(reportMetadataCopy, { columns: newColumns });
      setReportMetadata(reportMetadataCopy);
    }
  };

  const handleColumnFormClose = () => {
    setShowReportColumnForm(false);
    setReportColumnFormMode('');
    setReportColumnToOperateOn(null);
  };

  const getFilterByFromReportMetadata = (reportColumnAccessor: string) => {
    if (reportMetadata) {
      return reportMetadata.filter_by.find((reportFilter: ReportFilter) => {
        return reportColumnAccessor === reportFilter.field_name;
      });
    }
    return null;
  };

  const getNewFiltersFromReportForEditing = (
    reportColumnForEditing: ReportColumnForEditing
  ) => {
    if (!reportMetadata) {
      return null;
    }
    const reportMetadataCopy = { ...reportMetadata };
    let newReportFilters = reportMetadataCopy.filter_by;
    if (reportColumnForEditing.filterable) {
      const newReportFilter: ReportFilter = {
        field_name: reportColumnForEditing.accessor,
        field_value: reportColumnForEditing.filter_field_value,
        operator: reportColumnForEditing.filter_operator || 'equals',
      };
      const existingReportFilter = getFilterByFromReportMetadata(
        reportColumnForEditing.accessor
      );
      if (existingReportFilter) {
        const existingReportFilterIndex =
          reportMetadataCopy.filter_by.indexOf(existingReportFilter);
        if (reportColumnForEditing.filter_field_value) {
          newReportFilters[existingReportFilterIndex] = newReportFilter;
        } else {
          newReportFilters.splice(existingReportFilterIndex, 1);
        }
      } else if (reportColumnForEditing.filter_field_value) {
        newReportFilters = newReportFilters.concat([newReportFilter]);
      }
    }
    return newReportFilters;
  };

  const handleUpdateReportColumn = () => {
    if (reportColumnToOperateOn && reportMetadata) {
      const reportMetadataCopy = { ...reportMetadata };
      let newReportColumns = null;
      if (reportColumnFormMode === 'new') {
        newReportColumns = reportColumns().concat([reportColumnToOperateOn]);
      } else {
        newReportColumns = reportColumns().map((rc: ReportColumn) => {
          if (rc.accessor === reportColumnToOperateOn.accessor) {
            return reportColumnToOperateOn;
          }
          return rc;
        });
      }
      Object.assign(reportMetadataCopy, {
        columns: newReportColumns,
        filter_by: getNewFiltersFromReportForEditing(reportColumnToOperateOn),
      });
      setReportMetadata(reportMetadataCopy);
      setReportColumnToOperateOn(null);
      setShowReportColumnForm(false);
      setShowReportColumnForm(false);
    }
  };

  const reportColumnToReportColumnForEditing = (reportColumn: ReportColumn) => {
    const reportColumnForEditing: ReportColumnForEditing = Object.assign(
      reportColumn,
      { filter_field_value: '', filter_operator: '' }
    );
    const reportFilter = getFilterByFromReportMetadata(
      reportColumnForEditing.accessor
    );
    if (reportFilter) {
      reportColumnForEditing.filter_field_value = reportFilter.field_value;
      reportColumnForEditing.filter_operator =
        reportFilter.operator || 'equals';
    }
    return reportColumnForEditing;
  };

  const updateReportColumn = (event: any) => {
    const reportColumnForEditing = reportColumnToReportColumnForEditing(
      event.selectedItem
    );
    setReportColumnToOperateOn(reportColumnForEditing);
  };

  // options includes item and inputValue
  const shouldFilterReportColumn = (options: any) => {
    const reportColumn: ReportColumn = options.item;
    const { inputValue } = options;
    return (
      !reportColumnAccessors().includes(reportColumn.accessor) &&
      (reportColumn.accessor || '')
        .toLowerCase()
        .includes((inputValue || '').toLowerCase())
    );
  };

  const setReportColumnConditionValue = (event: any) => {
    if (reportColumnToOperateOn) {
      const reportColumnToOperateOnCopy = {
        ...reportColumnToOperateOn,
      };
      reportColumnToOperateOnCopy.filter_field_value = event.target.value;
      setReportColumnToOperateOn(reportColumnToOperateOnCopy);
    }
  };

  const reportColumnForm = () => {
    if (reportColumnFormMode === '') {
      return null;
    }
    const formElements = [
      <TextInput
        id="report-column-display-name"
        name="report-column-display-name"
        labelText="Display Name"
        disabled={!reportColumnToOperateOn}
        value={reportColumnToOperateOn ? reportColumnToOperateOn.Header : ''}
        onChange={(event: any) => {
          if (reportColumnToOperateOn) {
            const reportColumnToOperateOnCopy = {
              ...reportColumnToOperateOn,
            };
            reportColumnToOperateOnCopy.Header = event.target.value;
            setReportColumnToOperateOn(reportColumnToOperateOnCopy);
          }
        }}
      />,
    ];
    if (reportColumnToOperateOn && reportColumnToOperateOn.filterable) {
      formElements.push(
        <TextInput
          id="report-column-condition-value"
          name="report-column-condition-value"
          labelText="Condition Value"
          value={
            reportColumnToOperateOn
              ? reportColumnToOperateOn.filter_field_value
              : ''
          }
          onChange={setReportColumnConditionValue}
        />
      );
    }
    if (reportColumnFormMode === 'new') {
      formElements.push(
        <ComboBox
          onChange={updateReportColumn}
          className="combo-box-in-modal"
          id="report-column-selection"
          data-qa="report-column-selection"
          data-modal-primary-focus
          items={availableReportColumns}
          itemToString={(reportColumn: ReportColumn) => {
            if (reportColumn) {
              return reportColumn.accessor;
            }
            return null;
          }}
          shouldFilterItem={shouldFilterReportColumn}
          placeholder="Choose a column to show"
          titleText="Column"
        />
      );
    }
    const modalHeading =
      reportColumnFormMode === 'new'
        ? 'Add Column'
        : `Edit ${
            reportColumnToOperateOn ? reportColumnToOperateOn.accessor : ''
          } column`;
    return (
      <Modal
        open={showReportColumnForm}
        modalHeading={modalHeading}
        primaryButtonText="Save"
        primaryButtonDisabled={!reportColumnToOperateOn}
        onRequestSubmit={handleUpdateReportColumn}
        onRequestClose={handleColumnFormClose}
        hasScrollingContent
      >
        {formElements}
      </Modal>
    );
  };

  const columnSelections = () => {
    if (reportColumns()) {
      const tags: any = [];

      (reportColumns() as any).forEach((reportColumn: ReportColumn) => {
        const reportColumnForEditing =
          reportColumnToReportColumnForEditing(reportColumn);

        let tagType = 'cool-gray';
        let tagTypeClass = '';
        if (reportColumnForEditing.filterable) {
          tagType = 'green';
          tagTypeClass = 'tag-type-green';
        }
        let reportColumnLabel = reportColumnForEditing.Header;
        if (reportColumnForEditing.filter_field_value) {
          reportColumnLabel = `${reportColumnLabel}=${reportColumnForEditing.filter_field_value}`;
        }
        tags.push(
          <Tag type={tagType} size="sm">
            <Button
              kind="ghost"
              size="sm"
              className={`button-tag-icon ${tagTypeClass}`}
              title={`Edit ${reportColumnForEditing.accessor} column`}
              onClick={() => {
                setReportColumnToOperateOn(reportColumnForEditing);
                setShowReportColumnForm(true);
                setReportColumnFormMode('edit');
              }}
            >
              {reportColumnLabel}
            </Button>
            <Button
              data-qa="remove-report-column"
              renderIcon={Close}
              iconDescription="Remove Column"
              className={`button-tag-icon ${tagTypeClass}`}
              hasIconOnly
              size="sm"
              kind="ghost"
              onClick={() => removeColumn(reportColumnForEditing)}
            />
          </Tag>
        );
      });
      return (
        <Stack orientation="horizontal">
          {tags}
          <Button
            data-qa="add-column-button"
            renderIcon={AddAlt}
            iconDescription="Column options"
            className="with-tiny-top-margin"
            kind="ghost"
            hasIconOnly
            size="sm"
            onClick={() => {
              setShowReportColumnForm(true);
              setReportColumnFormMode('new');
            }}
          />
        </Stack>
      );
    }
    return null;
  };

  const filterOptions = () => {
    if (!showFilterOptions) {
      return null;
    }

    // get the columns anytime we display the filter options if they are empty
    if (availableReportColumns.length < 1) {
      HttpService.makeCallToBackend({
        path: `/process-instances/reports/columns`,
        successCallback: setAvailableReportColumns,
      });
    }

    return (
      <>
        <Grid fullWidth className="with-bottom-margin">
          <Column md={8} lg={16} sm={4}>
            <FormLabel>Columns</FormLabel>
            <br />
            {columnSelections()}
          </Column>
        </Grid>
        <Grid fullWidth className="with-bottom-margin">
          <Column md={8}>
            <ProcessModelSearch
              onChange={(selection: any) =>
                setProcessModelSelection(selection.selectedItem)
              }
              processModels={processModelAvailableItems}
              selectedItem={processModelSelection}
            />
          </Column>
          <Column md={8}>{processStatusSearch()}</Column>
        </Grid>
        <Grid fullWidth className="with-bottom-margin">
          <Column md={4}>
            {dateComponent(
              'Start date from',
              'start-from',
              startFromDate,
              startFromTime,
              setStartFromDate,
              setStartFromTime,
              startFromTimeInvalid,
              setStartFromTimeInvalid
            )}
          </Column>
          <Column md={4}>
            {dateComponent(
              'Start date to',
              'start-to',
              startToDate,
              startToTime,
              setStartToDate,
              setStartToTime,
              startToTimeInvalid,
              setStartToTimeInvalid
            )}
          </Column>
          <Column md={4}>
            {dateComponent(
              'End date from',
              'end-from',
              endFromDate,
              endFromTime,
              setEndFromDate,
              setEndFromTime,
              endFromTimeInvalid,
              setEndFromTimeInvalid
            )}
          </Column>
          <Column md={4}>
            {dateComponent(
              'End date to',
              'end-to',
              endToDate,
              endToTime,
              setEndToDate,
              setEndToTime,
              endToTimeInvalid,
              setEndToTimeInvalid
            )}
          </Column>
        </Grid>
        <Grid fullWidth className="with-bottom-margin">
          <Column sm={4} md={4} lg={8}>
            <ButtonSet>
              <Button
                kind=""
                className="button-white-background narrow-button"
                onClick={clearFilters}
              >
                Clear
              </Button>
              <Button
                kind="secondary"
                onClick={applyFilter}
                data-qa="filter-button"
                className="narrow-button"
              >
                Filter
              </Button>
            </ButtonSet>
          </Column>
          <Column sm={4} md={4} lg={8}>
            {saveAsReportComponent()}
          </Column>
        </Grid>
      </>
    );
  };

  const buildTable = () => {
    const headerLabels: Record<string, string> = {
      id: 'Id',
      process_model_identifier: 'Process',
      process_model_display_name: 'Process',
      start_in_seconds: 'Start Time',
      end_in_seconds: 'End Time',
      status: 'Status',
      username: 'Started By',
      spiff_step: 'SpiffWorkflow Step',
    };
    const getHeaderLabel = (header: string) => {
      return headerLabels[header] ?? header;
    };
    const headers = reportColumns().map((column: any) => {
      // return <th>{getHeaderLabel((column as any).Header)}</th>;
      return getHeaderLabel((column as any).Header);
    });

    const formatProcessInstanceId = (row: ProcessInstance, id: number) => {
      const modifiedProcessModelId: String =
        modifyProcessIdentifierForPathParam(row.process_model_identifier);
      return (
        <Link
          data-qa="process-instance-show-link"
          to={`/admin/process-instances/${modifiedProcessModelId}/${id}`}
          title={`View process instance ${id}`}
        >
          {id}
        </Link>
      );
    };
    const formatProcessModelIdentifier = (_row: any, identifier: any) => {
      return (
        <Link
          to={`/admin/process-models/${modifyProcessIdentifierForPathParam(
            identifier
          )}`}
        >
          {identifier}
        </Link>
      );
    };

    const formatSecondsForDisplay = (_row: any, seconds: any) => {
      return convertSecondsToFormattedDateTime(seconds) || '-';
    };
    const defaultFormatter = (_row: any, value: any) => {
      return value;
    };

    const reportColumnFormatters: Record<string, any> = {
      id: formatProcessInstanceId,
      process_model_identifier: formatProcessModelIdentifier,
      process_model_display_name: FormatProcessModelDisplayName,
      start_in_seconds: formatSecondsForDisplay,
      end_in_seconds: formatSecondsForDisplay,
    };
    const formattedColumn = (row: any, column: any) => {
      const formatter =
        reportColumnFormatters[column.accessor] ?? defaultFormatter;
      const value = row[column.accessor];
      if (column.accessor === 'status') {
        return (
          <td data-qa={`process-instance-status-${value}`}>
            {formatter(row, value)}
          </td>
        );
      }
      return <td>{formatter(row, value)}</td>;
    };

    const rows = processInstances.map((row: any) => {
      const currentRow = reportColumns().map((column: any) => {
        return formattedColumn(row, column);
      });
      return <tr key={row.id}>{currentRow}</tr>;
    });

    return (
      <Table size="lg">
        <TableHead>
          <TableRow>
            {headers.map((header: any) => (
              <TableHeader
                key={header}
                title={header === 'Id' ? 'Process Instance Id' : null}
              >
                {header}
              </TableHeader>
            ))}
          </TableRow>
        </TableHead>
        <tbody>{rows}</tbody>
      </Table>
    );
  };

  const toggleShowFilterOptions = () => {
    setShowFilterOptions(!showFilterOptions);
  };

  const reportSearchComponent = () => {
    if (showReports) {
      const columns = [
        <Column sm={2} md={4} lg={7}>
          <ProcessInstanceReportSearch
            onChange={processInstanceReportDidChange}
            selectedItem={processInstanceReportSelection}
          />
        </Column>,
      ];
      return (
        <Grid className="with-tiny-bottom-margin" fullWidth>
          {columns}
        </Grid>
      );
    }
    return null;
  };

  const filterComponent = () => {
    if (!filtersEnabled) {
      return null;
    }
    return (
      <>
        <Grid fullWidth>
          <Column sm={2} md={4} lg={7}>
            {reportSearchComponent()}
          </Column>
          <Column
            className="filterIcon"
            sm={{ span: 1, offset: 3 }}
            md={{ span: 1, offset: 7 }}
            lg={{ span: 1, offset: 15 }}
          >
            <Button
              data-qa="filter-section-expand-toggle"
              renderIcon={Filter}
              iconDescription="Filter Options"
              hasIconOnly
              size="lg"
              onClick={toggleShowFilterOptions}
            />
          </Column>
        </Grid>
        {filterOptions()}
      </>
    );
  };

  if (pagination && (!textToShowIfEmpty || pagination.total > 0)) {
    // eslint-disable-next-line prefer-const
    let { page, perPage } = getPageInfoFromSearchParams(
      searchParams,
      undefined,
      undefined,
      paginationQueryParamPrefix
    );
    if (perPageOptions && !perPageOptions.includes(perPage)) {
      // eslint-disable-next-line prefer-destructuring
      perPage = perPageOptions[1];
    }
    return (
      <>
        {reportColumnForm()}
        {processInstanceReportSaveTag()}
        {filterComponent()}
        <PaginationForTable
          page={page}
          perPage={perPage}
          pagination={pagination}
          tableToDisplay={buildTable()}
          paginationQueryParamPrefix={paginationQueryParamPrefix}
          perPageOptions={perPageOptions}
          paginationClassName={paginationClassName}
        />
      </>
    );
  }
  if (textToShowIfEmpty) {
    return (
      <p className="no-results-message with-large-bottom-margin">
        {textToShowIfEmpty}
      </p>
    );
  }

  return null;
}
