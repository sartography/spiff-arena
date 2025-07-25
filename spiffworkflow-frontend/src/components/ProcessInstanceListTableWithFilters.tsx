import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import { useTranslation } from 'react-i18next';
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
} from '@carbon/react';

import {
  Button as MuiButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Checkbox as MuiCheckbox,
  FormControl,
  FormControlLabel,
  InputLabel,
  Select,
  MenuItem,
  Autocomplete,
  TextField,
} from '@mui/material';
import { useDebouncedCallback } from 'use-debounce';
import {
  PROCESS_STATUSES,
  DATE_FORMAT_CARBON,
  DATE_FORMAT_FOR_DISPLAY,
} from '../config';
import {
  getKeyByValue,
  getPageInfoFromSearchParams,
  getProcessStatus,
  titleizeString,
  truncateString,
} from '../helpers';
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

// MUI
import ProcessModelSearchCarbon from './ProcessModelSearchCarbon';

import ProcessInstanceReportSearch from './ProcessInstanceReportSearch';
import ProcessInstanceListDeleteReport from './ProcessInstanceListDeleteReport';
import ProcessInstanceListSaveAsReport from './ProcessInstanceListSaveAsReport';
import { Notification } from './Notification';
import useAPIError from '../hooks/UseApiError';
import { usePermissionFetcher } from '../hooks/PermissionService';
import { Can } from '../contexts/Can';
import Filters from './Filters';
import DateAndTimeService from '../services/DateAndTimeService';
import ProcessInstanceListTable from './ProcessInstanceListTable';

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

interface DateParameters {
  [key: string]: ((..._args: any[]) => any)[];
}

export default function ProcessInstanceListTableWithFilters({
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

  const { t } = useTranslation();
  const { targetUris } = useUriListForPermissions();
  const permissionRequestData: PermissionsToCheck = {
    [targetUris.userSearch]: ['GET'],
  };
  const { ability, permissionsLoaded } = usePermissionFetcher(
    permissionRequestData,
  );
  const canSearchUsers: boolean = ability.can('GET', targetUris.userSearch);

  const [reportMetadata, setReportMetadata] = useState<ReportMetadata | null>(
    null,
  );

  const MAX_ITEMS_IN_DROPDOWN_FOR_USABILITY = 15;

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
  const [lastColumnFilter, setLastColumnFilter] = useState<string>('');

  const filterOperatorMappings: FilterOperatorMapping = {
    [t('filter_operator_is')]: { id: 'equals', requires_value: true },
    [t('filter_operator_is_not')]: { id: 'not_equals', requires_value: true },
    [t('filter_operator_contains')]: { id: 'contains', requires_value: true },
    [t('filter_operator_is_empty')]: { id: 'is_empty', requires_value: false },
    [t('filter_operator_is_not_empty')]: {
      id: 'is_not_empty',
      requires_value: false,
    },
  };

  const filterDisplayTypes: FilterDisplayTypeMapping = {
    date_time: t('filter_display_type_date_time'),
    duration: t('filter_display_type_duration'),
  };

  const processInstanceListPathPrefix =
    variant === 'all' ? '/process-instances/all' : '/process-instances/for-me';

  const [processStatusAllOptions, setProcessStatusAllOptions] = useState<any[]>(
    [],
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
  const [withRelationToMe, setWithRelationToMe] =
    useState<boolean>(showActionsColumn);
  const [systemReport, setSystemReport] = useState<string | null>(null);
  const [selectedUserGroup, setSelectedUserGroup] = useState<string | null>(
    null,
  );
  const [userGroups, setUserGroups] = useState<string[]>([]);
  const [selectedLastMilestone, setSelectedLastMilestone] = useState<
    string | null
  >(null);
  const [lastMilestones, setLastMilestones] = useState<string[]>([]);
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

  const lastRequestedInitatorSearchTerm = useRef<string>();

  const dateParametersToAlwaysFilterBy: DateParameters = useMemo(() => {
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

  // we apparently cannot use a state set in a useEffect from within that same useEffect
  // so use a variable instead
  const processModelSelectionItemsForUseEffect = useRef<ProcessModel[]>([]);

  const clearFilters = useCallback(() => {
    setEndFromDate('');
    setEndFromTime('');
    setEndToDate('');
    setEndToTime('');
    setProcessInitiatorSelection(null);
    setProcessModelSelection(null);
    setProcessStatusSelection([]);
    setSelectedUserGroup(null);
    setSelectedLastMilestone(null);
    setStartFromDate('');
    setStartFromTime('');
    setStartToDate('');
    setStartToTime('');
    setSystemReport(null);
    setWithOldestOpenTask(false);
    setWithRelationToMe(false);
    if (reportMetadata) {
      const reportMetadataCopy = { ...reportMetadata };
      reportMetadataCopy.filter_by = [];
      setReportMetadata(reportMetadataCopy);
    }
  }, [reportMetadata]);

  const setReportMetadataFromReport = useCallback(
    (processInstanceReport: ProcessInstanceReport | null = null) => {
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
          (rf: ReportFilter) => rf.field_name === 'with_oldest_open_task',
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
      clearFilters();

      // this is the code to re-populate the widgets on the page
      // with values from the report metadata, which is derived
      // from the searchParams (often report_hash)
      reportMetadataBodyToUse.filter_by.forEach(
        (reportFilter: ReportFilter) => {
          if (reportFilter.field_name === 'process_status') {
            setProcessStatusSelection(
              (reportFilter.field_value || '').split(','),
            );
          } else if (reportFilter.field_name === 'process_initiator_username') {
            setProcessInitiatorSelection(reportFilter.field_value || '');
          } else if (reportFilter.field_name === 'with_oldest_open_task') {
            setWithOldestOpenTask(reportFilter.field_value);
          } else if (reportFilter.field_name === 'with_relation_to_me') {
            setWithRelationToMe(reportFilter.field_value);
          } else if (reportFilter.field_name === 'user_group_identifier') {
            setSelectedUserGroup(reportFilter.field_value);
          } else if (reportFilter.field_name === 'last_milestone_bpmn_name') {
            setSelectedLastMilestone(reportFilter.field_value);
          } else if (systemReportOptions.includes(reportFilter.field_name)) {
            setSystemReport(reportFilter.field_name);
          } else if (reportFilter.field_name === 'process_model_identifier') {
            if (reportFilter.field_value) {
              processModelSelectionItemsForUseEffect.current.forEach(
                (processModel: ProcessModel) => {
                  if (processModel.id === reportFilter.field_value) {
                    setProcessModelSelection(processModel);
                  }
                },
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
                  reportFilter.field_value as any,
                );
              dateFunctionToCall(dateString);
              const timeString =
                DateAndTimeService.convertSecondsToFormattedTimeHoursMinutes(
                  reportFilter.field_value as any,
                );
              timeFunctionToCall(timeString);
            }
          }
        },
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
      setReportMetadata(reportMetadataBodyToUse);
    },
    [
      additionalReportFilters,
      clearFilters,
      dateParametersToAlwaysFilterBy,
      filtersEnabled,
      showActionsColumn,
      systemReportOptions,
    ],
  );

  // this is in its own callback to limit scrope of states we need to watch since
  // this function should never have to reload
  const getReportMetadataWithReportHash = useCallback(() => {
    const queryParams: string[] = [];

    // favor the reportHash state over the one in the searchParams
    if (reportHash) {
      queryParams.push(`report_hash=${reportHash}`);
    } else if (searchParams.get('report_hash')) {
      queryParams.push(`report_hash=${searchParams.get('report_hash')}`);
    }

    if (reportIdentifier) {
      queryParams.push(`report_identifier=${reportIdentifier}`);
    }
    if (searchParams.get('report_id')) {
      queryParams.push(`report_id=${searchParams.get('report_id')}`);
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
    // we only want to do this on initial load, after that, the table should take over.
    // the purpose of this api call is to get the initial report metadata. from there,
    // we incrementally change it based on filter widgets, which all happens client-side,
    // so we don't need to consult the server again after initial page load.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!permissionsLoaded) {
      return;
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
        },
      );
      setProcessStatusAllOptions(processStatusAllOptionsArray);

      // Fetch distinct milestone values for filtering
      HttpService.makeCallToBackend({
        path: `/process-instances/unique-milestone-names`,
        httpMethod: 'GET',
        successCallback: (lastMilestoneArray: string[]) => {
          setLastMilestones(lastMilestoneArray.sort());
        },
      });

      getReportMetadataWithReportHash();
    }
    const checkFiltersAndRun = () => {
      if (filtersEnabled) {
        // populate process model selection
        HttpService.makeCallToBackend({
          path: `/process-models?per_page=1500&recursive=true&include_parent_groups=true`,
          successCallback: processResultForProcessModels,
        });
      } else {
        getReportMetadataWithReportHash();
      }
    };

    checkFiltersAndRun();
  }, [
    filtersEnabled,
    getReportMetadataWithReportHash,
    permissionsLoaded,

    // watch the variant prop so when switching between the "For Me" and "All" pi list tables
    // the api call to find the new process instances is made and the report metadata is updated.
    variant,
  ]);

  const removeFieldFromReportMetadata = (
    reportMetadataToUse: ReportMetadata,
    fieldName: string,
  ) => {
    const filtersToKeep = reportMetadataToUse.filter_by.filter(
      (rf: ReportFilter) => rf.field_name !== fieldName,
    );

    reportMetadataToUse.filter_by = filtersToKeep;
  };

  const getFilterByFromReportMetadata = (
    reportColumnAccessor: string,
    reportMetadataToUse: ReportMetadata | null = reportMetadata,
  ) => {
    if (reportMetadataToUse) {
      return reportMetadataToUse.filter_by.find(
        (reportFilter: ReportFilter) => {
          return reportColumnAccessor === reportFilter.field_name;
        },
      );
    }
    return null;
  };

  const insertOrUpdateFieldInReportMetadata = (
    reportMetadataToUse: ReportMetadata,
    fieldName: string,
    fieldValue: any,
  ) => {
    // For milestone and user group, empty string means "remove the filter"
    if (
      fieldValue === '' &&
      (fieldName === 'last_milestone_bpmn_name' ||
        fieldName === 'user_group_identifier')
    ) {
      removeFieldFromReportMetadata(reportMetadataToUse, fieldName);
    } else if (fieldValue) {
      let existingReportFilter = getFilterByFromReportMetadata(
        fieldName,
        reportMetadataToUse,
      );
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
    const reportMetadataCopy = { ...reportMetadataToUse };
    setReportMetadata(reportMetadataCopy);
  };

  const handleProcessInstanceInitiatorSearchResult = (
    result: any,
    inputText: string,
  ) => {
    if (
      reportMetadata &&
      lastRequestedInitatorSearchTerm.current === result.username_prefix
    ) {
      setProcessInstanceInitiatorOptions(
        result.users.map((user: User) => user.username),
      );
      result.users.forEach((user: User) => {
        if (user.username === inputText) {
          const reportMetadataCopy = { ...reportMetadata };
          setReportMetadata(reportMetadataCopy);
          insertOrUpdateFieldInReportMetadata(
            reportMetadata,
            'process_initiator_username',
            user.username,
          );
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
    250,
  );

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
  const validateStartAndEndSeconds = () => {
    const startFromSeconds =
      DateAndTimeService.convertDateAndTimeStringsToSeconds(
        startFromDate,
        startFromTime || '00:00:00',
      );
    const startToSeconds =
      DateAndTimeService.convertDateAndTimeStringsToSeconds(
        startToDate,
        startToTime || '00:00:00',
      );
    const endFromSeconds =
      DateAndTimeService.convertDateAndTimeStringsToSeconds(
        endFromDate,
        endFromTime || '00:00:00',
      );
    const endToSeconds = DateAndTimeService.convertDateAndTimeStringsToSeconds(
      endToDate,
      endToTime || '00:00:00',
    );

    let message = '';
    if (isTrueComparison(startFromSeconds, '>', startToSeconds)) {
      message = t('filter_error_start_from_after_start_to');
    }
    if (isTrueComparison(endFromSeconds, '>', endToSeconds)) {
      message = t('filter_error_end_from_after_end_to');
    }
    if (isTrueComparison(startFromSeconds, '>', endFromSeconds)) {
      message = t('filter_error_start_after_end_from');
    }
    if (isTrueComparison(startToSeconds, '>', endToSeconds)) {
      message = t('filter_error_start_to_after_end_to');
    }
    if (message !== '') {
      addError({ message } as ErrorForDisplay);
    } else {
      removeError();
    }
  };

  const reportColumns = () => {
    if (reportMetadata) {
      return reportMetadata.columns;
    }
    return [];
  };

  const dateComponent = (
    labelTranslationKey: string,
    name: any,
    initialDate: any,
    initialTime: string,
    onChangeDateFunction: any,
    onChangeTimeFunction: any,
    timeInvalid: boolean,
    setTimeInvalid: any,
  ) => {
    if (!reportMetadata) {
      return null;
    }
    const propNameUnderscored = name.replaceAll('-', '_');
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
            labelText={t(labelTranslationKey)}
            type="text"
            size="md"
            autocomplete="off"
            allowInput={false}
            onChange={(dateChangeEvent: any) => {
              if (!initialDate && !initialTime) {
                onChangeTimeFunction(
                  DateAndTimeService.convertDateObjectToFormattedHoursMinutes(
                    new Date(),
                  ),
                );
              }
              const newValue =
                DateAndTimeService.convertDateAndTimeStringsToSeconds(
                  dateChangeEvent.srcElement.value,
                  initialTime || '00:00:00',
                );
              insertOrUpdateFieldInReportMetadata(
                reportMetadata,
                propNameUnderscored,
                newValue,
              );
              onChangeDateFunction(dateChangeEvent.srcElement.value);
              validateStartAndEndSeconds();
            }}
            value={initialDate}
          />
        </DatePicker>
        <TimePicker
          invalid={timeInvalid}
          id={`time-picker-${name}`}
          labelText={t('select_a_time')}
          pattern="^([01]\d|2[0-3]):?([0-5]\d)$"
          value={initialTime}
          onChange={(event: any) => {
            if (event.srcElement.validity.valid) {
              setTimeInvalid(false);
            } else {
              setTimeInvalid(true);
            }
            const newValue =
              DateAndTimeService.convertDateAndTimeStringsToSeconds(
                initialDate,
                event.srcElement.value,
              );
            insertOrUpdateFieldInReportMetadata(
              reportMetadata,
              propNameUnderscored,
              newValue,
            );
            onChangeTimeFunction(event.srcElement.value);
            validateStartAndEndSeconds();
          }}
        />
      </>
    );
  };

  const formatProcessInstanceStatus = (_row: any, value: any) => {
    return getProcessStatus(value);
  };

  const processStatusSearch = () => {
    if (!reportMetadata) {
      return null;
    }
    return (
      <MultiSelect
        label={t('choose_status')}
        className="our-class"
        id="process-instance-status-select"
        titleText={t('status')}
        items={processStatusAllOptions}
        onChange={(selection: any) => {
          insertOrUpdateFieldInReportMetadata(
            reportMetadata,
            'process_status',
            selection.selectedItems.join(','),
          );
          setProcessStatusSelection(selection.selectedItems);
        }}
        itemToString={(item: any) => {
          return formatProcessInstanceStatus(null, item);
        }}
        selectionFeedback="top-after-reopen"
        selectedItems={processStatusSelection}
      />
    );
  };

  const processInstanceReportDidChange = (
    selectedReport: any,
    mode?: string,
  ) => {
    clearFilters();
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
    processInstanceReport: ProcessInstanceReport,
  ) => {
    setProcessInstanceReportSelection(processInstanceReport);
    searchParams.set('report_id', processInstanceReport.id.toString());
    setSearchParams(searchParams);
  };

  const saveAsReportComponent = () => {
    return (
      <ProcessInstanceListSaveAsReport
        onSuccess={onSaveReportSuccess}
        buttonClassName="narrow-button"
        buttonText={t('save')}
        processInstanceReportSelection={processInstanceReportSelection}
        reportMetadata={reportMetadata}
      />
    );
  };

  const onDeleteReportSuccess = () => {
    processInstanceReportDidChange(undefined);
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
        (rc: ReportColumn) => rc.accessor !== reportColumn.accessor,
      );
      Object.assign(reportMetadataCopy, { columns: newColumns });
      const newFilters = reportMetadataCopy.filter_by.filter(
        (rf: ReportFilter) => rf.field_name !== reportColumn.accessor,
      );
      Object.assign(reportMetadataCopy, {
        columns: newColumns,
        filter_by: newFilters,
      });
      setReportMetadata(reportMetadataCopy);
    }
  };

  const handleColumnFormClose = () => {
    setShowReportColumnForm(false);
    setReportColumnFormMode('');
    setReportColumnToOperateOn(null);
  };

  const getFilterOperatorFromReportColumn = (
    reportColumnForEditing: ReportColumnForEditing,
  ) => {
    if (reportColumnForEditing.filter_operator) {
      return Object.entries(filterOperatorMappings).filter(([_key, value]) => {
        return value.id === reportColumnForEditing.filter_operator;
      })[0][1];
    }
    return null;
  };

  const getNewFiltersFromReportForEditing = (
    reportColumnForEditing: ReportColumnForEditing,
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
        reportColumnForEditing.accessor,
      );
      const filterOperator = getFilterOperatorFromReportColumn(
        reportColumnForEditing,
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
      let newReportColumns: ReportColumn[] = [];
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
    }
  };

  const reportColumnToReportColumnForEditing = (reportColumn: ReportColumn) => {
    const reportColumnForEditing: ReportColumnForEditing = Object.assign(
      reportColumn,
      { filter_field_value: '', filter_operator: '' },
    );
    if (reportColumn.filterable) {
      const reportFilter = getFilterByFromReportMetadata(
        reportColumnForEditing.accessor,
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
        event.selectedItem,
      );
    }
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

  const setReportColumnConditionOperator = (selectedItem: string) => {
    if (reportColumnToOperateOn) {
      const reportColumnToOperateOnCopy = {
        ...reportColumnToOperateOn,
      };
      const filterOperator = filterOperatorMappings[selectedItem];
      reportColumnToOperateOnCopy.filter_operator = filterOperator.id;
      setReportColumnToOperateOn(reportColumnToOperateOnCopy);
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
          key="report-column-selection"
          data-testid="report-column-selection"
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
        />,
      );
    }
    formElements.push([
      <TextInput
        id="report-column-display-name"
        key="report-column-display-name"
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
    ]);
    if (reportColumnToOperateOn && reportColumnToOperateOn.filterable) {
      formElements.push(
        <Dropdown
          titleText={t('display_type')}
          label={t('display_type')}
          id="report-column-display-type"
          key="report-column-display-type"
          items={[''].concat(Object.values(filterDisplayTypes))}
          selectedItem={
            reportColumnToOperateOn.display_type
              ? filterDisplayTypes[reportColumnToOperateOn.display_type]
              : ''
          }
          onChange={(value: any) => {
            setFilterDisplayType(value.selectedItem);
          }}
        />,
      );

      // if we pass undefined into selectedItem followed by an actual value then the component changes from uncontrolled
      // (i guess because selectedItem=undefined is treated the same as the parameter being omitted)
      // to controlled so get the operator here and use null if it's undefined
      const operator = getKeyByValue(
        filterOperatorMappings,
        reportColumnToOperateOn.filter_operator,
        'id',
      );
      formElements.push(
        <Dropdown
          titleText={t('operator_label')}
          label={t('operator_label')}
          id="report-column-condition-operator"
          items={Object.keys(filterOperatorMappings)}
          selectedItem={operator || null}
          onChange={(value: any) => {
            setReportColumnConditionOperator(value.selectedItem);
          }}
        />,
      );

      const filterOperator = getFilterOperatorFromReportColumn(
        reportColumnToOperateOn,
      );
      if (filterOperator && filterOperator.requires_value) {
        formElements.push(
          <TextInput
            id="report-column-condition-value"
            name="report-column-condition-value"
            labelText={t('condition_value')}
            value={
              reportColumnToOperateOn
                ? reportColumnToOperateOn.filter_field_value
                : ''
            }
            onChange={setReportColumnConditionValue}
          />,
        );
      }
    }
    formElements.push(
      <div className="vertical-spacer-to-allow-combo-box-to-expand-in-modal" />,
    );
    const modalHeading =
      reportColumnFormMode === 'new'
        ? t('add_column')
        : t('edit_column', {
            columnName: reportColumnToOperateOn
              ? reportColumnToOperateOn.accessor
              : '',
          });
    return (
      <Modal
        open={showReportColumnForm}
        modalHeading={modalHeading}
        primaryButtonText={t('save')}
        primaryButtonDisabled={!reportColumnToOperateOn}
        onRequestSubmit={handleUpdateReportColumn}
        onRequestClose={handleColumnFormClose}
        hasScrollingContent
        aria-label={modalHeading}
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
                title={t('edit_column', {
                  columnName: reportColumnForEditing.accessor,
                })}
                onClick={() => {
                  setReportColumnToOperateOn(reportColumnForEditing);
                  setShowReportColumnForm(true);
                  setReportColumnFormMode('edit');
                }}
              >
                {truncateString(reportColumnLabel, 10)}
              </Button>
              <Button
                data-testid="remove-report-column"
                renderIcon={Close}
                iconDescription={t('remove_column')}
                className={`button-tag-icon ${tagTypeClass}`}
                hasIconOnly
                size="sm"
                kind="ghost"
                onClick={() => removeColumn(reportColumnForEditing)}
              />
            </Tag>
          </Column>,
        );
      });
      return (
        <Grid narrow fullWidth className="filter-buttons">
          {tags}
          <Column md={1} lg={1} sm={1}>
            <Button
              data-testid="add-column-button"
              renderIcon={AddAlt}
              iconDescription={t('column_options')}
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
    if (!showAdvancedOptions || !reportMetadata) {
      return null;
    }
    return (
      <Dialog
        open={showAdvancedOptions}
        onClose={handleAdvancedOptionsClose}
        aria-labelledby="advanced-filter-options-title"
        fullWidth
        maxWidth="md"
      >
        <DialogTitle id="advanced-filter-options-title">
          {t('advanced_filter_options')}
        </DialogTitle>
        <DialogContent>
          <FormControl fullWidth margin="normal">
            <InputLabel id="system-report-label">
              {t('system_report')}
            </InputLabel>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <div style={{ flexGrow: 1 }}>
                <Select
                  fullWidth
                  labelId="system-report-label"
                  label={t('system_report')}
                  value={systemReport || ''}
                  onChange={(event) => {
                    const { value } = event.target;
                    systemReportOptions.forEach(
                      (systemReportOption: string) => {
                        insertOrUpdateFieldInReportMetadata(
                          reportMetadata,
                          systemReportOption,
                          value === systemReportOption,
                        );
                        setSystemReport(value);
                      },
                    );
                  }}
                >
                  {['', ...systemReportOptions].map((option) => (
                    <MenuItem key={option} value={option}>
                      {titleizeString(option)}
                    </MenuItem>
                  ))}
                </Select>
              </div>
              {systemReport && (
                <div style={{ marginLeft: '8px' }}>
                  <Button
                    onClick={() => {
                      systemReportOptions.forEach(
                        (systemReportOption: string) => {
                          insertOrUpdateFieldInReportMetadata(
                            reportMetadata,
                            systemReportOption,
                            false,
                          );
                        },
                      );
                      setSystemReport(null);
                    }}
                    size="sm"
                    kind="ghost"
                    hasIconOnly
                    renderIcon={Close}
                    iconDescription={t('clear_filter')}
                  />
                </div>
              )}
            </div>
          </FormControl>
          <FormControl fullWidth margin="normal">
            <InputLabel id="user-group-label">
              {t('assigned_user_group')}
            </InputLabel>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <div style={{ flexGrow: 1 }}>
                <Select
                  fullWidth
                  label={t('assigned_user_group')}
                  labelId="user-group-label"
                  value={selectedUserGroup || ''}
                  onChange={(event) => {
                    const { value } = event.target;
                    insertOrUpdateFieldInReportMetadata(
                      reportMetadata,
                      'user_group_identifier',
                      value,
                    );
                    setSelectedUserGroup(value);
                  }}
                >
                  {userGroups.map((group) => (
                    <MenuItem key={group} value={group}>
                      {group}
                    </MenuItem>
                  ))}
                </Select>
              </div>
              {selectedUserGroup && (
                <div style={{ marginLeft: '8px' }}>
                  <Button
                    onClick={() => {
                      insertOrUpdateFieldInReportMetadata(
                        reportMetadata,
                        'user_group_identifier',
                        '',
                      );
                      setSelectedUserGroup(null);
                    }}
                    size="sm"
                    kind="ghost"
                    hasIconOnly
                    renderIcon={Close}
                    iconDescription={t('clear_filter')}
                  />
                </div>
              )}
            </div>
          </FormControl>
          <FormControl fullWidth margin="normal">
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <div style={{ flexGrow: 1 }}>
                {lastMilestones.length > MAX_ITEMS_IN_DROPDOWN_FOR_USABILITY ? (
                  <Autocomplete
                    disablePortal
                    id="last-milestone-autocomplete"
                    options={lastMilestones}
                    value={selectedLastMilestone}
                    getOptionLabel={(option) => option || ''}
                    renderOption={(props, option) => (
                      <li {...props} key={option}>
                        {option}
                      </li>
                    )}
                    renderInput={(params) => (
                      <TextField
                        // Need props spreading for Autocomplete to work

                        {...params}
                        label={t('last_milestone')}
                        variant="outlined"
                        fullWidth
                      />
                    )}
                    onChange={(_event, value) => {
                      insertOrUpdateFieldInReportMetadata(
                        reportMetadata,
                        'last_milestone_bpmn_name',
                        value || '',
                      );
                      setSelectedLastMilestone(value);
                    }}
                  />
                ) : (
                  <>
                    <InputLabel id="last-milestone-label">
                      {t('last_milestone')}
                    </InputLabel>
                    <Select
                      fullWidth
                      label={t('last_milestone')}
                      labelId="last-milestone-label"
                      value={selectedLastMilestone || ''}
                      onChange={(event) => {
                        const { value } = event.target;
                        insertOrUpdateFieldInReportMetadata(
                          reportMetadata,
                          'last_milestone_bpmn_name',
                          value,
                        );
                        setSelectedLastMilestone(value);
                      }}
                    >
                      {lastMilestones.map((milestone) => (
                        <MenuItem key={milestone} value={milestone}>
                          {milestone}
                        </MenuItem>
                      ))}
                    </Select>
                  </>
                )}
              </div>
              {selectedLastMilestone && (
                <div style={{ marginLeft: '8px' }}>
                  <Button
                    onClick={() => {
                      insertOrUpdateFieldInReportMetadata(
                        reportMetadata,
                        'last_milestone_bpmn_name',
                        '',
                      );
                      setSelectedLastMilestone(null);
                    }}
                    size="sm"
                    kind="ghost"
                    hasIconOnly
                    renderIcon={Close}
                    iconDescription={t('clear_filter')}
                  />
                </div>
              )}
            </div>
          </FormControl>
          <FormControlLabel
            control={
              <MuiCheckbox
                checked={withOldestOpenTask}
                disabled={showActionsColumn}
                onChange={(event) => {
                  insertOrUpdateFieldInReportMetadata(
                    reportMetadata,
                    'with_oldest_open_task',
                    event.target.checked,
                  );
                  setWithOldestOpenTask(event.target.checked);
                }}
              />
            }
            label={t('include_oldest_open_task_information')}
          />
          {variant === 'all' && (
            <FormControlLabel
              control={
                <MuiCheckbox
                  checked={withRelationToMe}
                  onChange={(event) => {
                    insertOrUpdateFieldInReportMetadata(
                      reportMetadata,
                      'with_relation_to_me',
                      event.target.checked,
                    );
                    setWithRelationToMe(event.target.checked);
                  }}
                />
              }
              label={t('include_tasks_for_me')}
            />
          )}
        </DialogContent>
        <DialogActions>
          <MuiButton onClick={handleAdvancedOptionsClose} color="primary">
            {t('close')}
          </MuiButton>
        </DialogActions>
      </Dialog>
    );
  };

  const filterOptions = () => {
    if (!showFilterOptions || !reportMetadata) {
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
            <FormLabel>{t('columns_label')}</FormLabel>
            <br />
            {columnSelections()}
          </Column>
        </Grid>
        <Grid fullWidth className="with-bottom-margin">
          <Column md={8}>
            <ProcessModelSearchCarbon
              onChange={(selection: any) => {
                const pmSelectionId = selection.selectedItem
                  ? selection.selectedItem.id
                  : null;
                insertOrUpdateFieldInReportMetadata(
                  reportMetadata,
                  'process_model_identifier',
                  pmSelectionId,
                );
                setProcessModelSelection(selection.selectedItem);
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
                        insertOrUpdateFieldInReportMetadata(
                          reportMetadata,
                          'process_initiator_username',
                          event.selectedItem,
                        );
                        setProcessInitiatorSelection(event.selectedItem);
                      }}
                      id="process-instance-initiator-search"
                      data-testid="process-instance-initiator-search"
                      items={processInstanceInitiatorOptions}
                      placeholder={t('start_typing_username')}
                      titleText={t('started_by')}
                      selectedItem={processInitiatorSelection}
                    />
                  );
                }
                return (
                  <TextInput
                    id="process-instance-initiator-search"
                    placeholder={t('enter_username')}
                    labelText={t('started_by')}
                    onChange={(event: any) => {
                      insertOrUpdateFieldInReportMetadata(
                        reportMetadata,
                        'process_initiator_username',
                        event.target.value,
                      );
                      setProcessInitiatorSelection(event.target.value);
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
              t('filter_start_date_from'),
              'start-from',
              startFromDate,
              startFromTime,
              (val: string) => {
                setStartFromDate(val);
              },
              (val: string) => {
                setStartFromTime(val);
              },
              startFromTimeInvalid,
              setStartFromTimeInvalid,
            )}
          </Column>
          <Column md={4}>
            {dateComponent(
              t('filter_start_date_to'),
              'start-to',
              startToDate,
              startToTime,
              (val: string) => {
                setStartToDate(val);
              },
              (val: string) => {
                setStartToTime(val);
              },
              startToTimeInvalid,
              setStartToTimeInvalid,
            )}
          </Column>
          <Column md={4}>
            {dateComponent(
              t('filter_end_date_from'),
              'end-from',
              endFromDate,
              endFromTime,
              (val: string) => {
                setEndFromDate(val);
              },
              (val: string) => {
                setEndFromTime(val);
              },
              endFromTimeInvalid,
              setEndFromTimeInvalid,
            )}
          </Column>
          <Column md={4}>
            {dateComponent(
              t('filter_end_date_to'),
              'end-to',
              endToDate,
              endToTime,
              (val: string) => {
                setEndToDate(val);
              },
              (val: string) => {
                setEndToTime(val);
              },
              endToTimeInvalid,
              setEndToTimeInvalid,
            )}
          </Column>
        </Grid>
        <Grid fullWidth className="with-bottom-margin">
          <Column sm={4} md={4} lg={8}>
            <ButtonSet>
              <MuiButton variant="outlined" onClick={clearFilters}>
                {t('clear_button')}
              </MuiButton>
            </ButtonSet>
          </Column>
          <Column sm={3} md={3} lg={4}>
            <div style={{ display: 'flex', gap: '8px' }}>
              {saveAsReportComponent()}
              {deleteReportComponent()}
            </div>
          </Column>
          <Column sm={1} md={1} lg={1}>
            <Button
              kind="ghost"
              onClick={() => setShowAdvancedOptions(true)}
              data-testid="advanced-options-filters"
              className="narrow-button button-link"
            >
              {t('advanced')}
            </Button>
          </Column>
        </Grid>
      </>
    );
  };

  const reportSearchComponent = () => {
    if (showReports) {
      return (
        <Grid className="with-tiny-bottom-margin" fullWidth>
          <Column sm={4} md={8} lg={16}>
            <ProcessInstanceReportSearch
              onChange={processInstanceReportDidChange}
              selectedItem={processInstanceReportSelection}
              selectedReportId={searchParams.get('report_id')}
              handleSetSelectedReportCallback={
                setProcessInstanceReportSelection
              }
            />
          </Column>
        </Grid>
      );
    }
    return null;
  };

  const onProcessInstanceTableListUpdate = useCallback(
    (result: any) => {
      // mostly for pagination so we do not set the page to 1 if the report did not change
      if (result.report_hash && result.report_hash !== reportHash) {
        setReportHash(result.report_hash);
        const { page } = getPageInfoFromSearchParams(
          searchParams,
          undefined,
          undefined,
          paginationQueryParamPrefix,
        );
        if (page !== 1) {
          searchParams.set('page', '1');
          setSearchParams(searchParams);
        }
      }

      // if columns array is empty, assume the reportMetadata hasn't been fully set yet
      // either by a passed in prop or by the api server.
      // Note that reportMetadata is also never expected to be falsy here since the table cannot
      // render without and therefore this method would never get called.
      if (!reportMetadata || reportMetadata.columns.length === 0) {
        setReportMetadata(result.report_metadata);
      }
    },
    [
      reportHash,
      reportMetadata,
      searchParams,
      setSearchParams,
      paginationQueryParamPrefix,
    ],
  );

  const filterComponent = () => {
    return (
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
    );
  };

  let resultsTable = null;
  if (reportMetadata) {
    const refilterTextComponent = null;
    resultsTable = (
      <>
        {refilterTextComponent}
        <ProcessInstanceListTable
          autoReload={autoReloadEnabled}
          canCompleteAllTasks={canCompleteAllTasks}
          filterComponent={filterComponent}
          header={header}
          onProcessInstanceTableListUpdate={onProcessInstanceTableListUpdate}
          paginationClassName={paginationClassName}
          paginationQueryParamPrefix={paginationQueryParamPrefix}
          perPageOptions={perPageOptions}
          reportMetadata={reportMetadata}
          showActionsColumn={showActionsColumn}
          showLinkToReport={showLinkToReport}
          showRefreshButton
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
      {resultsTable}
    </div>
  );
}
