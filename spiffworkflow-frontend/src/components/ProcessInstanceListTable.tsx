import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { Close, AddAlt } from '@carbon/icons-react';
import {
  Button,
  ButtonSet,
  DatePicker,
  DatePickerInput,
  Dropdown,
  Grid,
  Column,
  MultiSelect,
  TimePicker,
  Tag,
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
import { getKeyByValue, titleizeString, truncateString } from '../helpers';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';

import 'react-datepicker/dist/react-datepicker.css';

import HttpService from '../services/HttpService';

import {
  ProcessModel,
  ProcessInstanceReport,
  ReportColumn,
  ReportColumnForEditing,
  ReportMetadata,
  ReportFilter,
  User,
  ErrorForDisplay,
  PermissionsToCheck,
  FilterOperatorMapping,
  FilterDisplayTypeMapping,
  SpiffTableHeader,
} from '../interfaces';
import ProcessModelSearch from './ProcessModelSearch';
import ProcessInstanceReportSearch from './ProcessInstanceReportSearch';
import ProcessInstanceListDeleteReport from './ProcessInstanceListDeleteReport';
import ProcessInstanceListSaveAsReport from './ProcessInstanceListSaveAsReport';
import { Notification } from './Notification';
import useAPIError from '../hooks/UseApiError';
import { usePermissionFetcher } from '../hooks/PermissionService';
import { Can } from '../contexts/Can';
import Filters from './Filters';
import DateAndTimeService from '../services/DateAndTimeService';
import ProcessInstanceListTableOnly from './ProcessInstanceListTableOnly';

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
  header?: SpiffTableHeader;
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
  header,
  tableHtmlId,
}: OwnProps) {
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
  const [applyFilterClicked, setApplyFilterClicked] = useState<boolean>(false);

  const [reportMetadata, setReportMetadata] = useState<ReportMetadata | null>();

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

  const filterOperatorMappings: FilterOperatorMapping = {
    Is: { id: 'equals', requires_value: true },
    'Is Not': { id: 'not_equals', requires_value: true },
    Contains: { id: 'contains', requires_value: true },
    'Is Empty': { id: 'is_empty', requires_value: false },
    'Is Not Empty': { id: 'is_not_empty', requires_value: false },
  };

  const filterDisplayTypes: FilterDisplayTypeMapping = {
    date_time: 'Date / time',
    duration: 'Duration',
  };

  const processInstanceListPathPrefix =
    variant === 'all' ? '/process-instances/all' : '/process-instances/for-me';

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
  const [autoReloadEnabled, setAutoReloadEnabled] =
    useState<boolean>(autoReload);

  const [showAdvancedOptions, setShowAdvancedOptions] =
    useState<boolean>(false);
  const [withOldestOpenTask, setWithOldestOpenTask] =
    useState<boolean>(showActionsColumn);
  const [withRelationToMe, setwithRelationToMe] =
    useState<boolean>(showActionsColumn);
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
    setwithRelationToMe(false);
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

  const setReportMetadataFromReport = useCallback(
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
      if (additionalReportFilters) {
        additionalReportFilters.forEach((arf: ReportFilter) => {
          if (!reportMetadataBodyToUse.filter_by.includes(arf)) {
            reportMetadataBodyToUse.filter_by.push(arf);
          }
        });
      }

      // If the showActionColumn is set to true, we need to include the with_oldest_open_task in the query params
      if (
        showActionsColumn &&
        !reportMetadataBodyToUse.filter_by.some(
          (rf: ReportFilter) => rf.field_name === 'with_oldest_open_task'
        )
      ) {
        const withOldestReportFilter = {
          field_name: 'with_oldest_open_task',
          field_value: true,
        };
        reportMetadataBodyToUse.filter_by.push(withOldestReportFilter);
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
          } else if (reportFilter.field_name === 'with_relation_to_me') {
            setwithRelationToMe(reportFilter.field_value);
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
              const dateString =
                DateAndTimeService.convertSecondsToFormattedDateString(
                  reportFilter.field_value as any
                );
              dateFunctionToCall(dateString);
              const timeString =
                DateAndTimeService.convertSecondsToFormattedTimeHoursMinutes(
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

      if (filtersEnabled) {
        HttpService.makeCallToBackend({
          path: `/user-groups/for-current-user`,
          successCallback: setUserGroups,
        });
      }
      setRequiresRefilter(false);
      setReportMetadata(reportMetadataBodyToUse);
    },
    [
      additionalReportFilters,
      clearFilters,
      dateParametersToAlwaysFilterBy,
      filtersEnabled,
      showActionsColumn,
      systemReportOptions,
    ]
  );

  useEffect(() => {
    if (!permissionsLoaded) {
      return;
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
          successCallback: setReportMetadataFromReport,
          onUnauthorized: () => setAutoReloadEnabled(false),
        });
      } else {
        setReportMetadataFromReport();
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
  }, [
    autoReload,
    filtersEnabled,
    setReportMetadataFromReport,
    permissionsLoaded,
    reportIdentifier,
    searchParams,
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
    const startFromSeconds =
      DateAndTimeService.convertDateAndTimeStringsToSeconds(
        startFromDate,
        startFromTime || '00:00:00'
      );
    const startToSeconds =
      DateAndTimeService.convertDateAndTimeStringsToSeconds(
        startToDate,
        startToTime || '00:00:00'
      );
    const endFromSeconds =
      DateAndTimeService.convertDateAndTimeStringsToSeconds(
        endFromDate,
        endFromTime || '00:00:00'
      );
    const endToSeconds = DateAndTimeService.convertDateAndTimeStringsToSeconds(
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
      'with_relation_to_me',
      withRelationToMe
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

    const newReportMetadata = getNewReportMetadataBasedOnPageWidgets();
    setReportMetadata(newReportMetadata);
    setApplyFilterClicked(true);
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
        <DatePicker
          id={`date-picker-parent-${name}`}
          dateFormat={DATE_FORMAT_CARBON}
          datePickerType="single"
        >
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
                  DateAndTimeService.convertDateObjectToFormattedHoursMinutes(
                    new Date()
                  )
                );
              }
              onChangeDateFunction(dateChangeEvent.srcElement.value);
            }}
            value={initialDate}
          />
        </DatePicker>
        <TimePicker
          invalid={timeInvalid}
          id={`time-picker-${name}`}
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
        successCallback: setReportMetadataFromReport,
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
      const newFilters = reportMetadataCopy.filter_by.filter(
        (rf: ReportFilter) => rf.field_name !== reportColumn.accessor
      );
      Object.assign(reportMetadataCopy, {
        columns: newColumns,
        filter_by: newFilters,
      });
      setReportMetadata(reportMetadataCopy);
      setRequiresRefilter(true);
    }
  };

  const handleColumnFormClose = () => {
    setShowReportColumnForm(false);
    setReportColumnFormMode('');
    setReportColumnToOperateOn(null);
  };

  const getFilterOperatorFromReportColumn = (
    reportColumnForEditing: ReportColumnForEditing
  ) => {
    if (reportColumnForEditing.filter_operator) {
      // eslint-disable-next-line prefer-destructuring
      return Object.entries(filterOperatorMappings).filter(([_key, value]) => {
        return value.id === reportColumnForEditing.filter_operator;
      })[0][1];
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
      const filterOperator = getFilterOperatorFromReportColumn(
        reportColumnForEditing
      );
      if (existingReportFilter) {
        const existingReportFilterIndex =
          reportMetadataCopy.filter_by.indexOf(existingReportFilter);
        if (filterOperator && !filterOperator.requires_value) {
          newReportFilter.field_value = '';
          newReportFilters[existingReportFilterIndex] = newReportFilter;
        } else if (reportColumnForEditing.filter_field_value) {
          newReportFilters[existingReportFilterIndex] = newReportFilter;
        } else {
          newReportFilters.splice(existingReportFilterIndex, 1);
        }
      } else if (filterOperator && !filterOperator.requires_value) {
        newReportFilter.field_value = '';
        newReportFilters = newReportFilters.concat([newReportFilter]);
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

  const setReportColumnConditionOperator = (selectedItem: string) => {
    if (reportColumnToOperateOn) {
      const reportColumnToOperateOnCopy = {
        ...reportColumnToOperateOn,
      };
      const filterOperator = filterOperatorMappings[selectedItem];
      reportColumnToOperateOnCopy.filter_operator = filterOperator.id;
      setReportColumnToOperateOn(reportColumnToOperateOnCopy);
      setRequiresRefilter(true);
    }
  };

  const setFilterDisplayType = (selectedItem: string) => {
    if (reportColumnToOperateOn) {
      const reportColumnToOperateOnCopy = {
        ...reportColumnToOperateOn,
      };
      const displayType = getKeyByValue(filterDisplayTypes, selectedItem);
      reportColumnToOperateOnCopy.display_type = displayType;
      setReportColumnToOperateOn(reportColumnToOperateOnCopy);
      setRequiresRefilter(true);
    }
  };

  // eslint-disable-next-line sonarjs/cognitive-complexity
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
        <Dropdown
          titleText="Display type"
          id="report-column-display-type"
          items={[''].concat(Object.values(filterDisplayTypes))}
          selectedItem={
            reportColumnToOperateOn.display_type
              ? filterDisplayTypes[reportColumnToOperateOn.display_type]
              : ''
          }
          onChange={(value: any) => {
            setFilterDisplayType(value.selectedItem);
            setRequiresRefilter(true);
          }}
        />
      );
      formElements.push(
        <Dropdown
          titleText="Operator"
          id="report-column-condition-operator"
          items={Object.keys(filterOperatorMappings)}
          selectedItem={getKeyByValue(
            filterOperatorMappings,
            reportColumnToOperateOn.filter_operator,
            'id'
          )}
          onChange={(value: any) => {
            setReportColumnConditionOperator(value.selectedItem);
            setRequiresRefilter(true);
          }}
        />
      );

      const filterOperator = getFilterOperatorFromReportColumn(
        reportColumnToOperateOn
      );
      if (filterOperator && filterOperator.requires_value) {
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
          <Column md={2} lg={2} sm={2}>
            <Tag type={tagType} size="sm" className="filter-tag">
              <Button
                kind="ghost"
                size="sm"
                className={`button-tag ${tagTypeClass}`}
                title={`Edit ${reportColumnForEditing.accessor} column`}
                onClick={() => {
                  setReportColumnToOperateOn(reportColumnForEditing);
                  setShowReportColumnForm(true);
                  setReportColumnFormMode('edit');
                }}
              >
                {truncateString(reportColumnLabel, 10)}
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
          </Column>
        );
      });
      return (
        <Grid narrow fullWidth className="filter-buttons">
          {tags}
          <Column md={1} lg={1} sm={1}>
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
          </Column>
        </Grid>
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
              disabled={showActionsColumn}
              onChange={(value: any) => {
                setWithOldestOpenTask(value.target.checked);
                setRequiresRefilter(true);
              }}
            />
          </Column>
          {variant === 'all' ? (
            <Column md={4} lg={8} sm={2}>
              <Checkbox
                labelText="Include tasks for me"
                id="with-relation-to-me"
                checked={withRelationToMe}
                onChange={(value: any) => {
                  setwithRelationToMe(value.target.checked);
                  setRequiresRefilter(true);
                }}
              />
            </Column>
          ) : null}
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

  const reportSearchComponent = () => {
    if (showReports) {
      const columns = [
        <Column sm={4} md={8} lg={16}>
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

  const onProcessInstanceTableListUpdate = (result: any) => {
    if (applyFilterClicked) {
      if (result.report_hash) {
        setReportHash(result.report_hash);
        searchParams.set('report_hash', result.report_hash);
        // whenever apply button is clicked, we want to reset the page to 1,
        // since the user has changed the filters
        if (requiresRefilter && searchParams.get('page') !== '1') {
          searchParams.set('page', '1');
        }
        setSearchParams(searchParams);
      }
      setApplyFilterClicked(false);
      setRequiresRefilter(false);
    }
  };

  let resultsTable = null;
  if (reportMetadata) {
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
        <ProcessInstanceListTableOnly
          autoReload={autoReloadEnabled}
          canCompleteAllTasks={canCompleteAllTasks}
          header={header}
          onProcessInstanceTableListUpdate={onProcessInstanceTableListUpdate}
          paginationClassName={paginationClassName}
          paginationQueryParamPrefix={paginationQueryParamPrefix}
          perPageOptions={perPageOptions}
          reportMetadata={reportMetadata}
          showActionsColumn={showActionsColumn}
          showLinkToReport={showLinkToReport}
          tableHtmlId={tableHtmlId}
          textToShowIfEmpty={textToShowIfEmpty}
          variant={variant}
        />
      </>
    );
  }

  return (
    <div className="process-instance-list-table">
      {reportColumnForm()}
      {advancedOptionsModal()}
      {processInstanceReportSaveTag()}
      <Grid fullWidth condensed className="megacondensed">
        <Column sm={{ span: 4 }} md={{ span: 8 }} lg={{ span: 16 }}>
          <Filters
            filterOptions={filterOptions}
            showFilterOptions={showFilterOptions}
            setShowFilterOptions={setShowFilterOptions}
            reportSearchComponent={reportSearchComponent}
            filtersEnabled={filtersEnabled}
            reportHash={reportHash}
          />
        </Column>
      </Grid>
      {resultsTable}
    </div>
  );
}
