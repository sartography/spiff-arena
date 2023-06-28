import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { Close, AddAlt, ArrowRight } from '@carbon/icons-react';
import {
  Button,
  ButtonSet,
  DatePicker,
  DatePickerInput,
  Dropdown,
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
  Checkbox,
} from '@carbon/react';
import { useDebouncedCallback } from 'use-debounce';
import {
  PROCESS_STATUSES,
  DATE_FORMAT_CARBON,
  DATE_FORMAT_FOR_DISPLAY,
} from '../config';
import {
  convertDateAndTimeStringsToSeconds,
  convertDateObjectToFormattedHoursMinutes,
  convertSecondsToFormattedDateString,
  convertSecondsToFormattedDateTime,
  convertSecondsToFormattedTimeHoursMinutes,
  getPageInfoFromSearchParams,
  modifyProcessIdentifierForPathParam,
  refreshAtInterval,
  REFRESH_INTERVAL_SECONDS,
  REFRESH_TIMEOUT_SECONDS,
  titleizeString,
} from '../helpers';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';

import PaginationForTable from './PaginationForTable';
import 'react-datepicker/dist/react-datepicker.css';

import HttpService from '../services/HttpService';

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
  paginationQueryParamPrefix?: string;
  perPageOptions?: number[];
  showReports?: boolean;
  reportIdentifier?: string;
  textToShowIfEmpty?: string;
  paginationClassName?: string;
  autoReload?: boolean;
  additionalReportFilters?: ReportFilter[];
  variant?: string;
  canCompleteAllTasks?: boolean;
  showActionsColumn?: boolean;
  showLinkToReport?: boolean;
  headerElement?: React.ReactElement;
  tableHtmlId?: string;
};

interface dateParameters {
  [key: string]: ((..._args: any[]) => any)[];
}

export default function ProcessInstanceListTable({
  filtersEnabled = true,
  paginationQueryParamPrefix,
  perPageOptions,
  additionalReportFilters,
  showReports = true,
  reportIdentifier,
  textToShowIfEmpty,
  paginationClassName,
  autoReload = false,
  variant = 'for-me',
  canCompleteAllTasks = false,
  showActionsColumn = false,
  showLinkToReport = false,
  headerElement,
  tableHtmlId,
}: OwnProps) {
  let processInstanceApiSearchPath = '/process-instances/for-me';
  if (variant === 'all') {
    processInstanceApiSearchPath = '/process-instances';
  }

  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const { addError, removeError } = useAPIError();

  const { targetUris } = useUriListForPermissions();
  const permissionRequestData: PermissionsToCheck = {
    [targetUris.userSearch]: ['GET'],
  };
  const { ability, permissionsLoaded } = usePermissionFetcher(
    permissionRequestData
  );
  const canSearchUsers: boolean = ability.can('GET', targetUris.userSearch);

  const [processInstances, setProcessInstances] = useState<ProcessInstance[]>(
    []
  );
  const [reportMetadata, setReportMetadata] = useState<ReportMetadata | null>();
  const [pagination, setPagination] = useState<PaginationObject | null>(null);

  const [startFromDate, setStartFromDate] = useState<string>('');
  const [startToDate, setStartToDate] = useState<string>('');
  const [endFromDate, setEndFromDate] = useState<string>('');
  const [endToDate, setEndToDate] = useState<string>('');
  const [startFromTime, setStartFromTime] = useState<string>('');
  const [startToTime, setStartToTime] = useState<string>('');
  const [endFromTime, setEndFromTime] = useState<string>('');
  const [endToTime, setEndToTime] = useState<string>('');
  const [startFromTimeInvalid, setStartFromTimeInvalid] =
    useState<boolean>(false);
  const [startToTimeInvalid, setStartToTimeInvalid] = useState<boolean>(false);
  const [endFromTimeInvalid, setEndFromTimeInvalid] = useState<boolean>(false);
  const [endToTimeInvalid, setEndToTimeInvalid] = useState<boolean>(false);

  const [showFilterOptions, setShowFilterOptions] = useState<boolean>(false);
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
  const [processInitiatorSelection, setProcessInitiatorSelection] = useState<
    string | null
  >(null);

  const [showAdvancedOptions, setShowAdvancedOptions] =
    useState<boolean>(false);
  const [withOldestOpenTask, setWithOldestOpenTask] = useState<boolean>(false);
  const [systemReport, setSystemReport] = useState<string | null>(null);
  const [selectedUserGroup, setSelectedUserGroup] = useState<string | null>(
    null
  );
  const [userGroups, setUserGroups] = useState<string[]>([]);
  const systemReportOptions: string[] = useMemo(() => {
    return [
      'instances_with_tasks_waiting_for_me',
      'instances_with_tasks_completed_by_me',
    ];
  }, []);

  // this is used from pages like the home page that have multiple tables
  // and cannot store the report hash in the query params.
  // it can be used to create a link to the process instances list page to reconstruct the report.
  const [reportHash, setReportHash] = useState<string | null>(null);

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
      setProcessInstanceInitiatorOptions(
        result.users.map((user: User) => user.username)
      );
      result.users.forEach((user: User) => {
        if (user.username === inputText) {
          setProcessInitiatorSelection(user.username);
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

  const addDebouncedSearchProcessInitiator = useDebouncedCallback(
    (value: string) => {
      searchForProcessInitiator(value);
    },
    // delay in ms
    250
  );

  const setProcessInstancesFromResult = useCallback((result: any) => {
    setRequiresRefilter(false);
    const processInstancesFromApi = result.results;
    setProcessInstances(processInstancesFromApi);
    setPagination(result.pagination);

    setReportMetadata(result.report_metadata);
    if (result.report_hash) {
      setReportHash(result.report_hash);
    }
  }, []);

  const setProcessInstancesFromApplyFilter = (result: any) => {
    setProcessInstancesFromResult(result);
    if (result.report_hash) {
      searchParams.set('report_hash', result.report_hash);
      setSearchParams(searchParams);
    }
  };

  // Useful to stop refreshing if an api call gets an error
  // since those errors can make the page unusable in any way
  const clearRefreshRef = useRef<any>(null);
  const stopRefreshing = useCallback((error: any) => {
    if (clearRefreshRef.current) {
      clearRefreshRef.current();
    }
    if (error) {
      console.error(error);
    }
  }, []);

  // we apparently cannot use a state set in a useEffect from within that same useEffect
  // so use a variable instead
  const processModelSelectionItemsForUseEffect = useRef<ProcessModel[]>([]);

  const clearFilters = useCallback((updateRequiresRefilter: boolean = true) => {
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
    setProcessInitiatorSelection(null);
    setWithOldestOpenTask(false);
    setSystemReport(null);
    setSelectedUserGroup(null);
    if (updateRequiresRefilter) {
      setRequiresRefilter(true);
    }
    if (reportMetadata) {
      reportMetadata.filter_by = [];
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const getProcessInstances = useCallback(
    (
      processInstanceReport: ProcessInstanceReport | null = null
      // eslint-disable-next-line sonarjs/cognitive-complexity
    ) => {
      let reportMetadataBodyToUse: ReportMetadata = {
        columns: [],
        filter_by: [],
        order_by: [],
      };
      if (processInstanceReport) {
        reportMetadataBodyToUse = processInstanceReport.report_metadata;
        if (processInstanceReport.id > 0) {
          setProcessInstanceReportSelection(processInstanceReport);
        }
      }

      // a bit hacky, clear out all filters before setting them from report metadata
      // to ensure old filters are cleared out.
      // this is really for going between the 'For Me' and 'All' tabs.
      clearFilters(false);

      // this is the code to re-populate the widgets on the page
      // with values from the report metadata, which is derived
      // from the searchParams (often report_hash)
      reportMetadataBodyToUse.filter_by.forEach(
        (reportFilter: ReportFilter) => {
          if (reportFilter.field_name === 'process_status') {
            setProcessStatusSelection(
              (reportFilter.field_value || '').split(',')
            );
          } else if (reportFilter.field_name === 'process_initiator_username') {
            setProcessInitiatorSelection(reportFilter.field_value || '');
          } else if (reportFilter.field_name === 'with_oldest_open_task') {
            setWithOldestOpenTask(reportFilter.field_value);
          } else if (reportFilter.field_name === 'user_group_identifier') {
            setSelectedUserGroup(reportFilter.field_value);
          } else if (systemReportOptions.includes(reportFilter.field_name)) {
            setSystemReport(reportFilter.field_name);
          } else if (reportFilter.field_name === 'process_model_identifier') {
            if (reportFilter.field_value) {
              processModelSelectionItemsForUseEffect.current.forEach(
                (processModel: ProcessModel) => {
                  if (processModel.id === reportFilter.field_value) {
                    setProcessModelSelection(processModel);
                  }
                }
              );
            }
          } else if (dateParametersToAlwaysFilterBy[reportFilter.field_name]) {
            const dateFunctionToCall =
              dateParametersToAlwaysFilterBy[reportFilter.field_name][0];
            const timeFunctionToCall =
              dateParametersToAlwaysFilterBy[reportFilter.field_name][1];
            if (reportFilter.field_value) {
              const dateString = convertSecondsToFormattedDateString(
                reportFilter.field_value as any
              );
              dateFunctionToCall(dateString);
              const timeString = convertSecondsToFormattedTimeHoursMinutes(
                reportFilter.field_value as any
              );
              timeFunctionToCall(timeString);
            }
          }
        }
      );

      if (reportMetadataBodyToUse.filter_by.length > 1) {
        setShowFilterOptions(true);
      }

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
      const queryParamString = `per_page=${perPage}&page=${page}`;
      if (additionalReportFilters) {
        additionalReportFilters.forEach((arf: ReportFilter) => {
          if (!reportMetadataBodyToUse.filter_by.includes(arf)) {
            reportMetadataBodyToUse.filter_by.push(arf);
          }
        });
      }

      if (filtersEnabled) {
        HttpService.makeCallToBackend({
          path: `/user-groups/for-current-user`,
          successCallback: setUserGroups,
        });
      }

      HttpService.makeCallToBackend({
        path: `${processInstanceApiSearchPath}?${queryParamString}`,
        successCallback: setProcessInstancesFromResult,
        httpMethod: 'POST',
        failureCallback: stopRefreshing,
        onUnauthorized: stopRefreshing,
        postBody: {
          report_metadata: reportMetadataBodyToUse,
        },
      });
    },
    [
      additionalReportFilters,
      dateParametersToAlwaysFilterBy,
      filtersEnabled,
      paginationQueryParamPrefix,
      perPageOptions,
      processInstanceApiSearchPath,
      searchParams,
      setProcessInstancesFromResult,
      stopRefreshing,
      systemReportOptions,
      clearFilters,
    ]
  );

  useEffect(() => {
    if (!permissionsLoaded) {
      return undefined;
    }
    function getReportMetadataWithReportHash() {
      const queryParams: string[] = [];
      ['report_hash', 'report_id'].forEach((paramName: string) => {
        if (searchParams.get(paramName)) {
          queryParams.push(`${paramName}=${searchParams.get(paramName)}`);
        }
      });
      if (reportIdentifier) {
        queryParams.push(`report_identifier=${reportIdentifier}`);
      }

      if (queryParams.length > 0) {
        const queryParamString = `?${queryParams.join('&')}`;
        HttpService.makeCallToBackend({
          path: `/process-instances/report-metadata${queryParamString}`,
          successCallback: getProcessInstances,
          onUnauthorized: stopRefreshing,
        });
      } else {
        getProcessInstances();
      }
    }
    function processResultForProcessModels(result: any) {
      const selectionArray = result.results.map((item: any) => {
        const label = `${item.id}`;
        Object.assign(item, { label });
        return item;
      });
      processModelSelectionItemsForUseEffect.current = selectionArray;
      setProcessModelAvailableItems(selectionArray);

      const processStatusAllOptionsArray = PROCESS_STATUSES.map(
        (processStatusOption: any) => {
          return processStatusOption;
        }
      );
      setProcessStatusAllOptions(processStatusAllOptionsArray);

      getReportMetadataWithReportHash();
    }
    const checkFiltersAndRun = () => {
      if (filtersEnabled) {
        // populate process model selection
        HttpService.makeCallToBackend({
          path: `/process-models?per_page=1000&recursive=true&include_parent_groups=true`,
          successCallback: processResultForProcessModels,
        });
      } else {
        getReportMetadataWithReportHash();
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
    filtersEnabled,
    getProcessInstances,
    permissionsLoaded,
    reportIdentifier,
    searchParams,
    stopRefreshing,
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

  const reportColumns = () => {
    if (reportMetadata) {
      return reportMetadata.columns;
    }
    return [];
  };

  const removeFieldFromReportMetadata = (
    reportMetadataToUse: ReportMetadata,
    fieldName: string
  ) => {
    const filtersToKeep = reportMetadataToUse.filter_by.filter(
      (rf: ReportFilter) => rf.field_name !== fieldName
    );
    // eslint-disable-next-line no-param-reassign
    reportMetadataToUse.filter_by = filtersToKeep;
  };

  const getFilterByFromReportMetadata = (reportColumnAccessor: string) => {
    if (reportMetadata) {
      return reportMetadata.filter_by.find((reportFilter: ReportFilter) => {
        return reportColumnAccessor === reportFilter.field_name;
      });
    }
    return null;
  };

  const insertOrUpdateFieldInReportMetadata = (
    reportMetadataToUse: ReportMetadata,
    fieldName: string,
    fieldValue: any
  ) => {
    if (fieldValue) {
      let existingReportFilter = getFilterByFromReportMetadata(fieldName);
      if (existingReportFilter) {
        existingReportFilter.field_value = fieldValue;
      } else {
        existingReportFilter = {
          field_name: fieldName,
          field_value: fieldValue,
          operator: 'equals',
        };
        reportMetadataToUse.filter_by.push(existingReportFilter);
      }
    } else {
      removeFieldFromReportMetadata(reportMetadataToUse, fieldName);
    }
  };

  const getNewReportMetadataBasedOnPageWidgets = () => {
    const {
      valid,
      startFromSeconds,
      startToSeconds,
      endFromSeconds,
      endToSeconds,
    } = calculateStartAndEndSeconds();

    if (!valid) {
      return null;
    }

    let newReportMetadata: ReportMetadata | null = null;
    if (reportMetadata) {
      newReportMetadata = { ...reportMetadata };
    }
    if (!newReportMetadata) {
      newReportMetadata = {
        columns: [],
        filter_by: [],
        order_by: [],
      };
    }

    insertOrUpdateFieldInReportMetadata(
      newReportMetadata,
      'start_from',
      startFromSeconds
    );
    insertOrUpdateFieldInReportMetadata(
      newReportMetadata,
      'start_to',
      startToSeconds
    );
    insertOrUpdateFieldInReportMetadata(
      newReportMetadata,
      'end_from',
      endFromSeconds
    );
    insertOrUpdateFieldInReportMetadata(
      newReportMetadata,
      'end_to',
      endToSeconds
    );

    insertOrUpdateFieldInReportMetadata(
      newReportMetadata,
      'process_status',
      processStatusSelection.length > 0
        ? processStatusSelection.join(',')
        : null
    );
    insertOrUpdateFieldInReportMetadata(
      newReportMetadata,
      'process_model_identifier',
      processModelSelection ? processModelSelection.id : null
    );
    insertOrUpdateFieldInReportMetadata(
      newReportMetadata,
      'process_initiator_username',
      processInitiatorSelection
    );

    insertOrUpdateFieldInReportMetadata(
      newReportMetadata,
      'with_oldest_open_task',
      withOldestOpenTask
    );
    insertOrUpdateFieldInReportMetadata(
      newReportMetadata,
      'user_group_identifier',
      selectedUserGroup
    );
    systemReportOptions.forEach((systemReportOption: string) => {
      if (newReportMetadata) {
        insertOrUpdateFieldInReportMetadata(
          newReportMetadata,
          systemReportOption,
          systemReport === systemReportOption
        );
      }
    });

    return newReportMetadata;
  };

  const applyFilter = (event: any) => {
    event.preventDefault();
    setProcessInitiatorNotFoundErrorText('');

    // eslint-disable-next-line prefer-const
    let { page, perPage } = getPageInfoFromSearchParams(
      searchParams,
      undefined,
      undefined,
      paginationQueryParamPrefix
    );
    page = 1;

    const newReportMetadata = getNewReportMetadataBasedOnPageWidgets();
    setReportMetadata(newReportMetadata);

    const queryParamString = `per_page=${perPage}&page=${page}`;
    HttpService.makeCallToBackend({
      path: `${processInstanceApiSearchPath}?${queryParamString}`,
      httpMethod: 'POST',
      postBody: { report_metadata: newReportMetadata },
      failureCallback: stopRefreshing,
      onUnauthorized: stopRefreshing,
      successCallback: (result: any) => {
        setProcessInstancesFromApplyFilter(result);
      },
    });
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
            placeholder={DATE_FORMAT_FOR_DISPLAY}
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

  const formatProcessInstanceStatus = (_row: any, value: any) => {
    return titleizeString((value || '').replaceAll('_', ' '));
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
          setRequiresRefilter(true);
        }}
        itemToString={(item: any) => {
          return formatProcessInstanceStatus(null, item);
        }}
        selectionFeedback="top-after-reopen"
        selectedItems={processStatusSelection}
      />
    );
  };

  const processInstanceReportDidChange = (selection: any, mode?: string) => {
    clearFilters();
    const selectedReport = selection.selectedItem;
    setProcessInstanceReportSelection(selectedReport);
    removeError();
    setProcessInstanceReportJustSaved(mode || null);

    let queryParamString = '';
    if (selectedReport) {
      queryParamString = `?report_id=${selectedReport.id}`;

      HttpService.makeCallToBackend({
        path: `/process-instances/report-metadata${queryParamString}`,
        successCallback: getProcessInstances,
      });
    }
    navigate(`${processInstanceListPathPrefix}${queryParamString}`);
  };

  const reportColumnAccessors = () => {
    return reportColumns().map((reportColumn: ReportColumn) => {
      return reportColumn.accessor;
    });
  };

  const onSaveReportSuccess = (
    processInstanceReport: ProcessInstanceReport
  ) => {
    setProcessInstanceReportSelection(processInstanceReport);
    searchParams.set('report_id', processInstanceReport.id.toString());
    setSearchParams(searchParams);
  };

  const saveAsReportComponent = () => {
    return (
      <ProcessInstanceListSaveAsReport
        onSuccess={onSaveReportSuccess}
        buttonClassName="button-white-background narrow-button"
        buttonText="Save"
        processInstanceReportSelection={processInstanceReportSelection}
        getReportMetadataCallback={getNewReportMetadataBasedOnPageWidgets}
      />
    );
  };

  const onDeleteReportSuccess = () => {
    processInstanceReportDidChange({ selectedItem: null });
  };

  const deleteReportComponent = () => {
    return processInstanceReportSelection ? (
      <ProcessInstanceListDeleteReport
        onSuccess={onDeleteReportSuccess}
        processInstanceReportSelection={processInstanceReportSelection}
      />
    ) : null;
  };

  const removeColumn = (reportColumn: ReportColumn) => {
    if (reportMetadata) {
      const reportMetadataCopy = { ...reportMetadata };
      const newColumns = reportColumns().filter(
        (rc: ReportColumn) => rc.accessor !== reportColumn.accessor
      );
      Object.assign(reportMetadataCopy, { columns: newColumns });
      setReportMetadata(reportMetadataCopy);
      setRequiresRefilter(true);
    }
  };

  const handleColumnFormClose = () => {
    setShowReportColumnForm(false);
    setReportColumnFormMode('');
    setReportColumnToOperateOn(null);
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
      setRequiresRefilter(true);
    }
  };

  const reportColumnToReportColumnForEditing = (reportColumn: ReportColumn) => {
    const reportColumnForEditing: ReportColumnForEditing = Object.assign(
      reportColumn,
      { filter_field_value: '', filter_operator: '' }
    );
    if (reportColumn.filterable) {
      const reportFilter = getFilterByFromReportMetadata(
        reportColumnForEditing.accessor
      );
      if (reportFilter) {
        reportColumnForEditing.filter_field_value =
          reportFilter.field_value || '';
        reportColumnForEditing.filter_operator =
          reportFilter.operator || 'equals';
      }
    }
    return reportColumnForEditing;
  };

  const updateReportColumn = (event: any) => {
    let reportColumnForEditing = null;
    if (event.selectedItem) {
      reportColumnForEditing = reportColumnToReportColumnForEditing(
        event.selectedItem
      );
    }
    setReportColumnToOperateOn(reportColumnForEditing);
    setRequiresRefilter(true);
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
      setRequiresRefilter(true);
    }
  };

  const reportColumnForm = () => {
    if (reportColumnFormMode === '') {
      return null;
    }
    const formElements = [];
    if (reportColumnFormMode === 'new') {
      formElements.push(
        <ComboBox
          onChange={updateReportColumn}
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
          selectedItem={reportColumnToOperateOn}
        />
      );
    }
    formElements.push([
      <TextInput
        id="report-column-display-name"
        name="report-column-display-name"
        labelText="Display Name"
        disabled={!reportColumnToOperateOn}
        value={reportColumnToOperateOn ? reportColumnToOperateOn.Header : ''}
        onChange={(event: any) => {
          if (reportColumnToOperateOn) {
            setRequiresRefilter(true);
            const reportColumnToOperateOnCopy = {
              ...reportColumnToOperateOn,
            };
            reportColumnToOperateOnCopy.Header = event.target.value;
            setReportColumnToOperateOn(reportColumnToOperateOnCopy);
          }
        }}
      />,
    ]);
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
    formElements.push(
      <div className="vertical-spacer-to-allow-combo-box-to-expand-in-modal" />
    );
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
    if (reportColumns().length > 0) {
      const tags: any = [];
      reportColumns().forEach((reportColumn: ReportColumn) => {
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

  const handleAdvancedOptionsClose = () => {
    setShowAdvancedOptions(false);
  };

  const advancedOptionsModal = () => {
    if (!showAdvancedOptions) {
      return null;
    }
    const formElements = (
      <>
        <Grid fullWidth>
          <Column md={4} lg={8} sm={2}>
            <Dropdown
              id="system-report-dropdown"
              titleText="System report"
              items={['', ...systemReportOptions]}
              itemToString={(item: any) => titleizeString(item)}
              selectedItem={systemReport}
              onChange={(value: any) => {
                setSystemReport(value.selectedItem);
                setRequiresRefilter(true);
              }}
            />
          </Column>
          <Column md={4} lg={8} sm={2}>
            <Dropdown
              id="user-group-dropdown"
              titleText="Assigned user group"
              items={['', ...userGroups]}
              itemToString={(item: any) => item}
              selectedItem={selectedUserGroup}
              onChange={(value: any) => {
                setSelectedUserGroup(value.selectedItem);
                setRequiresRefilter(true);
              }}
            />
          </Column>
        </Grid>
        <br />
        <Grid fullWidth>
          <Column md={4} lg={8} sm={2}>
            <Checkbox
              labelText="Include oldest open task information"
              id="with-oldest-open-task-checkbox"
              checked={withOldestOpenTask}
              onChange={(value: any) => {
                setWithOldestOpenTask(value.target.checked);
                setRequiresRefilter(true);
              }}
            />
          </Column>
        </Grid>
        <div className="vertical-spacer-to-allow-combo-box-to-expand-in-modal" />
      </>
    );
    return (
      <Modal
        open={showAdvancedOptions}
        modalHeading="Advanced filter options"
        primaryButtonText="Close"
        onRequestSubmit={handleAdvancedOptionsClose}
        onRequestClose={handleAdvancedOptionsClose}
        hasScrollingContent
        size="lg"
      >
        {formElements}
      </Modal>
    );
  };

  const filterOptions = () => {
    if (!showFilterOptions) {
      return null;
    }

    let queryParamString = '';
    if (processModelSelection) {
      queryParamString += `?process_model_identifier=${processModelSelection.id}`;
    }
    // get the columns anytime we display the filter options if they are empty.
    // and if the columns are not empty, check if the columns are stale
    // because we selected a different process model in the filter options.
    const columnFilterIsStale = lastColumnFilter !== queryParamString;
    if (availableReportColumns.length < 1 || columnFilterIsStale) {
      setLastColumnFilter(queryParamString);
      HttpService.makeCallToBackend({
        path: `/process-instances/reports/columns${queryParamString}`,
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
              onChange={(selection: any) => {
                setProcessModelSelection(selection.selectedItem);
                setRequiresRefilter(true);
              }}
              processModels={processModelAvailableItems}
              selectedItem={processModelSelection}
              truncateProcessModelDisplayName
            />
          </Column>
          <Column md={4}>
            <Can
              I="GET"
              a={targetUris.userSearch}
              ability={ability}
              passThrough
            >
              {(hasAccess: boolean) => {
                if (hasAccess) {
                  return (
                    <ComboBox
                      onInputChange={addDebouncedSearchProcessInitiator}
                      onChange={(event: any) => {
                        setProcessInitiatorSelection(event.selectedItem);
                        setRequiresRefilter(true);
                      }}
                      id="process-instance-initiator-search"
                      data-qa="process-instance-initiator-search"
                      items={processInstanceInitiatorOptions}
                      itemToString={(processInstanceInitatorOption: User) => {
                        if (processInstanceInitatorOption) {
                          return processInstanceInitatorOption;
                        }
                        return null;
                      }}
                      placeholder="Start typing username"
                      titleText="Started by"
                      selectedItem={processInitiatorSelection}
                    />
                  );
                }
                return (
                  <TextInput
                    id="process-instance-initiator-search"
                    placeholder="Enter username"
                    labelText="Started by"
                    invalid={processInitiatorNotFoundErrorText !== ''}
                    invalidText={processInitiatorNotFoundErrorText}
                    onChange={(event: any) => {
                      setProcessInitiatorSelection(event.target.value);
                      setRequiresRefilter(true);
                    }}
                  />
                );
              }}
            </Can>
          </Column>
          <Column md={4}>{processStatusSearch()}</Column>
        </Grid>
        <Grid fullWidth className="with-bottom-margin">
          <Column md={4}>
            {dateComponent(
              'Start date from',
              'start-from',
              startFromDate,
              startFromTime,
              (val: string) => {
                setStartFromDate(val);
                setRequiresRefilter(true);
              },
              (val: string) => {
                setStartFromTime(val);
                setRequiresRefilter(true);
              },
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
              (val: string) => {
                setStartToDate(val);
                setRequiresRefilter(true);
              },
              (val: string) => {
                setStartToTime(val);
                setRequiresRefilter(true);
              },
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
              (val: string) => {
                setEndFromDate(val);
                setRequiresRefilter(true);
              },
              (val: string) => {
                setEndFromTime(val);
                setRequiresRefilter(true);
              },
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
              (val: string) => {
                setEndToDate(val);
                setRequiresRefilter(true);
              },
              (val: string) => {
                setEndToTime(val);
                setRequiresRefilter(true);
              },
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
                disabled={!requiresRefilter}
                onClick={applyFilter}
                data-qa="filter-button"
                className="narrow-button"
              >
                Apply
              </Button>
            </ButtonSet>
          </Column>
          <Column sm={3} md={3} lg={7}>
            {saveAsReportComponent()}
            {deleteReportComponent()}
          </Column>
          <Column sm={1} md={1} lg={1}>
            <Button
              kind="ghost"
              onClick={() => setShowAdvancedOptions(true)}
              data-qa="advanced-options-filters"
              className="narrow-button button-link float-right"
            >
              Advanced
            </Button>
          </Column>
        </Grid>
      </>
    );
  };

  const getWaitingForTableCellComponent = (processInstanceTask: any) => {
    let fullUsernameString = '';
    let shortUsernameString = '';
    if (processInstanceTask.potential_owner_usernames) {
      fullUsernameString = processInstanceTask.potential_owner_usernames;
      const usernames =
        processInstanceTask.potential_owner_usernames.split(',');
      const firstTwoUsernames = usernames.slice(0, 2);
      if (usernames.length > 2) {
        firstTwoUsernames.push('...');
      }
      shortUsernameString = firstTwoUsernames.join(',');
    }
    if (processInstanceTask.assigned_user_group_identifier) {
      fullUsernameString = processInstanceTask.assigned_user_group_identifier;
      shortUsernameString = processInstanceTask.assigned_user_group_identifier;
    }
    return <span title={fullUsernameString}>{shortUsernameString}</span>;
  };
  const formatProcessInstanceId = (row: ProcessInstance, id: number) => {
    return <span data-qa="paginated-entity-id">{id}</span>;
  };
  const formatProcessModelIdentifier = (_row: any, identifier: any) => {
    return <span>{identifier}</span>;
  };
  const formatProcessModelDisplayName = (_row: any, identifier: any) => {
    return <span>{identifier}</span>;
  };

  const formatSecondsForDisplay = (_row: any, seconds: any) => {
    return convertSecondsToFormattedDateTime(seconds) || '-';
  };
  const defaultFormatter = (_row: any, value: any) => {
    return value;
  };

  const formattedColumn = (row: ProcessInstance, column: ReportColumn) => {
    const reportColumnFormatters: Record<string, any> = {
      id: formatProcessInstanceId,
      process_model_identifier: formatProcessModelIdentifier,
      process_model_display_name: formatProcessModelDisplayName,
      status: formatProcessInstanceStatus,
      start_in_seconds: formatSecondsForDisplay,
      end_in_seconds: formatSecondsForDisplay,
      updated_at_in_seconds: formatSecondsForDisplay,
      task_updated_at_in_seconds: formatSecondsForDisplay,
    };
    const columnAccessor = column.accessor as keyof ProcessInstance;
    const formatter =
      reportColumnFormatters[columnAccessor] ?? defaultFormatter;
    const value = row[columnAccessor];

    if (columnAccessor === 'status') {
      return (
        <td data-qa={`process-instance-status-${value}`}>
          {formatter(row, value)}
        </td>
      );
    }
    if (columnAccessor === 'process_model_display_name') {
      return <td> {formatter(row, value)} </td>;
    }
    if (columnAccessor === 'waiting_for') {
      return <td> {getWaitingForTableCellComponent(row)} </td>;
    }
    if (columnAccessor === 'updated_at_in_seconds') {
      return (
        <TableCellWithTimeAgoInWords
          timeInSeconds={row.updated_at_in_seconds}
        />
      );
    }
    if (columnAccessor === 'task_updated_at_in_seconds') {
      return (
        <TableCellWithTimeAgoInWords
          timeInSeconds={row.task_updated_at_in_seconds || 0}
        />
      );
    }
    return (
      // eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions
      <td data-qa={`process-instance-show-link-${columnAccessor}`}>
        {formatter(row, value)}
      </td>
    );
  };

  // eslint-disable-next-line sonarjs/cognitive-complexity
  const buildTable = () => {
    const headers = reportColumns().map((column: ReportColumn) => {
      return column.Header;
    });
    if (showActionsColumn) {
      headers.push('Action');
    }

    const rows = processInstances.map((processInstance: ProcessInstance) => {
      const currentRow = reportColumns().map((column: ReportColumn) => {
        return formattedColumn(processInstance, column);
      });
      if (showActionsColumn) {
        let buttonElement = null;
        const taskShowUrl = `/tasks/${processInstance.id}/${processInstance.task_id}`;
        const regex = new RegExp(`\\b(${preferredUsername}|${userEmail})\\b`);
        let hasAccessToCompleteTask = false;
        if (
          canCompleteAllTasks ||
          (processInstance.potential_owner_usernames || '').match(regex)
        ) {
          hasAccessToCompleteTask = true;
        }
        buttonElement = null;
        if (hasAccessToCompleteTask && processInstance.task_id) {
          buttonElement = (
            <Button
              kind="secondary"
              href={taskShowUrl}
              style={{ width: '60px' }}
            >
              Go
            </Button>
          );
        }

        if (
          processInstance.status === 'not_started' ||
          processInstance.status === 'user_input_required' ||
          processInstance.status === 'waiting' ||
          processInstance.status === 'complete'
        ) {
          currentRow.push(<td>{buttonElement}</td>);
        } else {
          currentRow.push(<td />);
        }
      }

      const rowStyle = { cursor: 'pointer' };
      const modifiedModelId = modifyProcessIdentifierForPathParam(
        processInstance.process_model_identifier
      );
      const navigateToProcessInstance = () => {
        navigate(
          `${processInstanceShowPathPrefix}/${modifiedModelId}/${processInstance.id}`
        );
      };
      return (
        // eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions
        <tr
          style={rowStyle}
          key={processInstance.id}
          onClick={navigateToProcessInstance}
          onKeyDown={navigateToProcessInstance}
        >
          {currentRow}
        </tr>
      );
    });

    let tableProps: any = { size: 'lg' };
    if (tableHtmlId) {
      tableProps = { ...tableProps, id: tableHtmlId };
    }

    return (
      // eslint-disable-next-line react/jsx-props-no-spreading
      <Table {...tableProps}>
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

  const reportSearchComponent = () => {
    if (showReports) {
      const columns = [
        <Column sm={2} md={4} lg={7}>
          <ProcessInstanceReportSearch
            onChange={processInstanceReportDidChange}
            selectedItem={processInstanceReportSelection}
            selectedReportId={searchParams.get('report_id')}
            handleSetSelectedReportCallback={setProcessInstanceReportSelection}
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

  const tableTitleLine = () => {
    if (!showLinkToReport && !headerElement) {
      return null;
    }
    let filterButtonLink = null;
    if (showLinkToReport && processInstances.length > 0) {
      filterButtonLink = (
        <Column
          sm={{ span: 1, offset: 3 }}
          md={{ span: 1, offset: 7 }}
          lg={{ span: 1, offset: 15 }}
          style={{ textAlign: 'right' }}
        >
          <Button
            data-qa="process-instance-list-link"
            renderIcon={ArrowRight}
            iconDescription="View Filterable List"
            hasIconOnly
            size="lg"
            onClick={() =>
              navigate(`/admin/process-instances?report_hash=${reportHash}`)
            }
          />
        </Column>
      );
    }
    return (
      <>
        <Column sm={{ span: 3 }} md={{ span: 7 }} lg={{ span: 15 }}>
          {headerElement}
        </Column>
        {filterButtonLink}
      </>
    );
  };

  let resultsTable = null;
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
    resultsTable = (
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
  } else if (textToShowIfEmpty) {
    resultsTable = (
      <p className="no-results-message with-large-bottom-margin">
        {textToShowIfEmpty}
      </p>
    );
  }

  return (
    <>
      {reportColumnForm()}
      {advancedOptionsModal()}
      {processInstanceReportSaveTag()}
      <Grid fullWidth condensed>
        {tableTitleLine()}
        <Column sm={{ span: 16 }} md={{ span: 16 }} lg={{ span: 16 }}>
          <Filters
            filterOptions={filterOptions}
            showFilterOptions={showFilterOptions}
            setShowFilterOptions={setShowFilterOptions}
            reportSearchComponent={reportSearchComponent}
            filtersEnabled={filtersEnabled}
          />
        </Column>
        <Column sm={{ span: 16 }} md={{ span: 16 }} lg={{ span: 16 }}>
          {resultsTable}
        </Column>
      </Grid>
    </>
  );
}
