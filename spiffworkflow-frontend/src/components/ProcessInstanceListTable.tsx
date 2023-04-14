import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';

// @ts-ignore
import { Close, AddAlt } from '@carbon/icons-react';
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
  encodeBase64,
  getPageInfoFromSearchParams,
  getProcessModelFullIdentifierFromSearchParams,
  modifyProcessIdentifierForPathParam,
  refreshAtInterval,
  REFRESH_INTERVAL_SECONDS,
  REFRESH_TIMEOUT_SECONDS,
} from '../helpers';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';

import PaginationForTable from './PaginationForTable';
import 'react-datepicker/dist/react-datepicker.css';

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
  User,
  ErrorForDisplay,
  PermissionsToCheck,
} from '../interfaces';
import ProcessModelSearch from './ProcessModelSearch';
import ProcessInstanceReportSearch from './ProcessInstanceReportSearch';
import ProcessInstanceListDeleteReport from './ProcessInstanceListDeleteReport';
import ProcessInstanceListSaveAsReport from './ProcessInstanceListSaveAsReport';
import { Notification } from './Notification';
import useAPIError from '../hooks/UseApiError';
import { usePermissionFetcher } from '../hooks/PermissionService';
import { Can } from '../contexts/Can';
import TableCellWithTimeAgoInWords from './TableCellWithTimeAgoInWords';
import UserService from '../services/UserService';
import Filters from './Filters';

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
  variant?: string;
  canCompleteAllTasks?: boolean;
  showActionsColumn?: boolean;
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
  variant = 'for-me',
  canCompleteAllTasks = false,
  showActionsColumn = false,
}: OwnProps) {
  let apiPath = '/process-instances/for-me';
  if (variant === 'all') {
    apiPath = '/process-instances';
  }
  const params = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { addError, removeError } = useAPIError();

  const { targetUris } = useUriListForPermissions();
  const permissionRequestData: PermissionsToCheck = {
    [targetUris.userSearch]: ['GET'],
  };
  const { ability } = usePermissionFetcher(permissionRequestData);
  const canSearchUsers: boolean = ability.can('GET', targetUris.userSearch);

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
  const [requiresRefilter, setRequiresRefilter] = useState<boolean>(false);
  const [lastColumnFilter, setLastColumnFilter] = useState<string>('');

  const preferredUsername = UserService.getPreferredUsername();
  const userEmail = UserService.getUserEmail();

  const processInstanceListPathPrefix =
    variant === 'all'
      ? '/admin/process-instances/all'
      : '/admin/process-instances/for-me';
  const processInstanceShowPathPrefix =
    variant === 'all'
      ? '/admin/process-instances'
      : '/admin/process-instances/for-me';

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

  const [processInstanceInitiatorOptions, setProcessInstanceInitiatorOptions] =
    useState<string[]>([]);
  const [processInitiatorSelection, setProcessInitiatorSelection] =
    useState<User | null>(null);
  const [processInitiatorText, setProcessInitiatorText] = useState<
    string | null
  >(null);
  const [
    processInitiatorNotFoundErrorText,
    setProcessInitiatorNotFoundErrorText,
  ] = useState<string>('');

  const lastRequestedInitatorSearchTerm = useRef<string>();

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

  const handleProcessInstanceInitiatorSearchResult = (
    result: any,
    inputText: string
  ) => {
    if (lastRequestedInitatorSearchTerm.current === result.username_prefix) {
      setProcessInstanceInitiatorOptions(result.users);
      result.users.forEach((user: User) => {
        if (user.username === inputText) {
          setProcessInitiatorSelection(user);
        }
      });
    }
  };

  const searchForProcessInitiator = (inputText: string) => {
    if (inputText && canSearchUsers) {
      lastRequestedInitatorSearchTerm.current = inputText;
      HttpService.makeCallToBackend({
        path: `/users/search?username_prefix=${inputText}`,
        successCallback: (result: any) =>
          handleProcessInstanceInitiatorSearchResult(result, inputText),
      });
    }
  };

  const parametersToGetFromSearchParams = useMemo(() => {
    const figureOutProcessInitiator = (processInitiatorSearchText: string) => {
      searchForProcessInitiator(processInitiatorSearchText);
    };

    return {
      process_model_identifier: null,
      process_status: null,
      process_initiator_username: figureOutProcessInitiator,
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const clearRefreshRef = useRef<any>(null);

  // eslint-disable-next-line sonarjs/cognitive-complexity
  useEffect(() => {
    function setProcessInstancesFromResult(result: any) {
      setRequiresRefilter(false);
      const processInstancesFromApi = result.results;
      setProcessInstances(processInstancesFromApi);
      setPagination(result.pagination);
      setProcessInstanceFilters(result.filters);

      setReportMetadata(result.report.report_metadata);
      if (result.report.id) {
        setProcessInstanceReportSelection(result.report);
      }
    }
    const stopRefreshing = () => {
      if (clearRefreshRef.current) {
        clearRefreshRef.current();
      }
    };
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

      if (searchParams.get('report_columns')) {
        queryParamString += `&report_columns=${searchParams.get(
          'report_columns'
        )}`;
      }
      if (searchParams.get('report_filter_by')) {
        queryParamString += `&report_filter_by=${searchParams.get(
          'report_filter_by'
        )}`;
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
        path: `${apiPath}?${queryParamString}`,
        successCallback: setProcessInstancesFromResult,
        onUnauthorized: stopRefreshing,
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
          path: `/process-models?per_page=1000&recursive=true&include_parent_groups=true`,
          successCallback: processResultForProcessModels,
        });
      } else {
        getProcessInstances();
      }
    };

    checkFiltersAndRun();
    if (autoReload) {
      clearRefreshRef.current = refreshAtInterval(
        REFRESH_INTERVAL_SECONDS,
        REFRESH_TIMEOUT_SECONDS,
        checkFiltersAndRun
      );
      return clearRefreshRef.current;
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
    apiPath,
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

    if (filters.process_initiator_username) {
      const functionToCall =
        parametersToGetFromSearchParams.process_initiator_username;
      functionToCall(filters.process_initiator_username);
    }

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

  // jasquat/burnettk - 2022-12-28 do not check the validity of the dates when rendering components to avoid the page being
  // re-rendered while the user is still typing. NOTE that we also prevented rerendering
  // with the use of the setErrorMessageSafely function. we are not sure why the context not
  // changing still causes things to rerender when we call its setter without our extra check.
  const calculateStartAndEndSeconds = (validate: boolean = true) => {
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

    if (validate) {
      let message = '';
      if (isTrueComparison(startFromSeconds, '>', startToSeconds)) {
        message = '"Start date from" cannot be after "start date to"';
      }
      if (isTrueComparison(endFromSeconds, '>', endToSeconds)) {
        message = '"End date from" cannot be after "end date to"';
      }
      if (isTrueComparison(startFromSeconds, '>', endFromSeconds)) {
        message = '"Start date from" cannot be after "end date from"';
      }
      if (isTrueComparison(startToSeconds, '>', endToSeconds)) {
        message = '"Start date to" cannot be after "end date to"';
      }
      if (message !== '') {
        valid = false;
        addError({ message } as ErrorForDisplay);
      }
    }

    return {
      valid,
      startFromSeconds,
      startToSeconds,
      endFromSeconds,
      endToSeconds,
    };
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
    let refilterTextComponent = null;
    if (requiresRefilter) {
      refilterTextComponent = (
        <p className="please-press-filter-button">
          * Please press the Apply button when you have completed updating the
          filters.
        </p>
      );
    }
    const resultsTable = (
      <>
        {refilterTextComponent}
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
    return (
      <>
        {reportColumnForm()}
        {processInstanceReportSaveTag()}
        <Filters
          filterOptions={filterOptions()}
          showFilterOptions={showFilterOptions}
          setShowFilterOptions={setShowFilterOptions}
          reportSearchComponent={reportSearchComponent}
          filtersEnabled={filtersEnabled}
        />
        {resultsTable}
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
