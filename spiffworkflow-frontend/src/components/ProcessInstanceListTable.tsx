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
import { useDebouncedCallback } from 'use-debounce';
import {
  PROCESS_STATUSES,
  DATE_FORMAT_CARBON,
  DATE_FORMAT_FOR_DISPLAY,
} from '../config';
import {
  capitalizeFirstLetter,
  convertDateAndTimeStringsToSeconds,
  convertDateObjectToFormattedHoursMinutes,
  convertSecondsToFormattedDateString,
  convertSecondsToFormattedDateTime,
  convertSecondsToFormattedTimeHoursMinutes,
  decodeBase64,
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
  let processInstanceApiSearchPath = '/process-instances/for-me';
  if (variant === 'all') {
    processInstanceApiSearchPath = '/process-instances';
  }
  const params = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
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

  const [listHasBeenFiltered, setListHasBeenFiltered] =
    useState<boolean>(false);

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

  const addDebouncedSearchProcessInitiator = useDebouncedCallback(
    (value: string) => {
      searchForProcessInitiator(value);
    },
    // delay in ms
    250
  );

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
    if (result.report_hash) {
      searchParams.set('report_hash', result.report_hash);
      setSearchParams(searchParams);
    }
  }

  const clearRefreshRef = useRef<any>(null);
  const stopRefreshing = (error: any) => {
    if (clearRefreshRef.current) {
      clearRefreshRef.current();
    }
    if (error) {
      console.error(error);
    }
  };

  // eslint-disable-next-line sonarjs/cognitive-complexity
  useEffect(() => {
    // we apparently cannot use a state set in a useEffect from within that same useEffect
    // so use a variable instead
    let processModelSelectionItemsForUseEffect: ProcessModel[] = [];

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

    // Useful to stop refreshing if an api call gets an error
    // since those errors can make the page unusable in any way
    const stopRefreshing = (error: any) => {
      if (clearRefreshRef.current) {
        clearRefreshRef.current();
      }
      if (error) {
        console.error(error);
      }
    };
    function getProcessInstances(
      reportMetadataBody: ReportMetadata | null = null
    ) {
      if (listHasBeenFiltered) {
        return;
      }
      let reportMetadataBodyToUse = reportMetadataBody;
      if (!reportMetadataBodyToUse) {
        reportMetadataBodyToUse = {
          columns: [],
          filter_by: [],
          order_by: [],
        };
      }

      let selectedProcessModelIdentifier = processModelFullIdentifier;
      reportMetadataBodyToUse.filter_by.forEach(
        (reportFilter: ReportFilter) => {
          if (reportFilter.field_name === 'process_status') {
            setProcessStatusSelection(
              (reportFilter.field_value || '').split(',')
            );
          } else if (reportFilter.field_name === 'process_model_identifier') {
            selectedProcessModelIdentifier =
              reportFilter.field_value || undefined;
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
              setShowFilterOptions(true);
            }
          }
        }
      );

      processModelSelectionItemsForUseEffect.forEach(
        (processModel: ProcessModel) => {
          if (processModel.id === selectedProcessModelIdentifier) {
            setProcessModelSelection(processModel);
          }
        }
      );

      // const postBody: ReportMetadata = {
      //   columns: [],
      //   filter_by: [],
      //   order_by: [],
      // };
      //
      // if (searchParams.get('report_id')) {
      //   queryParamString += `&report_id=${searchParams.get('report_id')}`;
      // } else if (reportIdentifier) {
      //   queryParamString += `&report_identifier=${reportIdentifier}`;
      // }

      // if (searchParams.get('report_columns')) {
      //   const reportColumnsBase64 = searchParams.get('report_columns');
      //   if (reportColumnsBase64) {
      //     const reportColumnsList = JSON.parse(
      //       decodeBase64(reportColumnsBase64)
      //     );
      //     postBody.columns = reportColumnsList;
      //   }
      // }
      // if (searchParams.get('report_filter_by')) {
      //   const reportFilterByBase64 = searchParams.get('report_filter_by');
      //   if (reportFilterByBase64) {
      //     const reportFilterByList = JSON.parse(
      //       decodeBase64(reportFilterByBase64)
      //     );
      //     postBody.filter_by = reportFilterByList;
      //   }
      // }
      //
      // Object.keys(parametersToGetFromSearchParams).forEach(
      //   (paramName: string) => {
      //     if (
      //       paramName === 'process_model_identifier' &&
      //       processModelFullIdentifier
      //     ) {
      //       postBody.filter_by.push({
      //         field_name: 'process_model_identifier',
      //         field_value: processModelFullIdentifier,
      //       });
      //     } else if (searchParams.get(paramName)) {
      //       // @ts-expect-error TS(7053) FIXME:
      //       const functionToCall = parametersToGetFromSearchParams[paramName];
      //       postBody.filter_by.push({
      //         field_name: paramName,
      //         field_value: searchParams.get(paramName),
      //       });
      //       if (functionToCall !== null) {
      //         functionToCall(searchParams.get(paramName) || '');
      //       }
      //       setShowFilterOptions(true);
      //     }
      //   }
      // );

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
      if (additionalParams) {
        queryParamString += `&${additionalParams}`;
      }

      HttpService.makeCallToBackend({
        path: `${processInstanceApiSearchPath}?${queryParamString}`,
        successCallback: setProcessInstancesFromResult,
        httpMethod: 'POST',
        failureCallback: stopRefreshing,
        onUnauthorized: stopRefreshing,
        postBody: {
          report_metadata: reportMetadataBody,
        },
      });
    }
    function getReportMetadataWithReportHash() {
      if (listHasBeenFiltered) {
        return;
      }
      const reportHash = searchParams.get('report_hash');
      if (reportHash) {
        HttpService.makeCallToBackend({
          path: `/process-instances/report-metadata/${reportHash}`,
          successCallback: getProcessInstances,
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
      processModelSelectionItemsForUseEffect = selectionArray;
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
    processInstanceApiSearchPath,
  ]);

  // // This sets the filter data using the saved reports returned from the initial instance_list query.
  // // This could probably be merged into the main useEffect but it works here now.
  // useEffect(() => {
  //   const filters = processInstanceFilters as any;
  //   // Object.keys(dateParametersToAlwaysFilterBy).forEach((paramName: string) => {
  //   //   const dateFunctionToCall = dateParametersToAlwaysFilterBy[paramName][0];
  //   //   const timeFunctionToCall = dateParametersToAlwaysFilterBy[paramName][1];
  //   //   const paramValue = filters[paramName];
  //   //   dateFunctionToCall('');
  //   //   timeFunctionToCall('');
  //   //   if (paramValue) {
  //   //     const dateString = convertSecondsToFormattedDateString(
  //   //       paramValue as any
  //   //     );
  //   //     dateFunctionToCall(dateString);
  //   //     const timeString = convertSecondsToFormattedTimeHoursMinutes(
  //   //       paramValue as any
  //   //     );
  //   //     timeFunctionToCall(timeString);
  //   //     setShowFilterOptions(true);
  //   //   }
  //   // });
  //
  //   // setProcessModelSelection(null);
  //   // processModelAvailableItems.forEach((item: any) => {
  //   //   if (item.id === filters.process_model_identifier) {
  //   //     setProcessModelSelection(item);
  //   //   }
  //   // });
  //
  //   if (filters.process_initiator_username) {
  //     const functionToCall =
  //       parametersToGetFromSearchParams.process_initiator_username;
  //     functionToCall(filters.process_initiator_username);
  //   }
  //
  //   const processStatusSelectedArray: string[] = [];
  //   if (filters.process_status) {
  //     PROCESS_STATUSES.forEach((processStatusOption: any) => {
  //       const regex = new RegExp(`\\b${processStatusOption}\\b`);
  //       if (filters.process_status.match(regex)) {
  //         processStatusSelectedArray.push(processStatusOption);
  //       }
  //     });
  //     setShowFilterOptions(true);
  //   }
  //   // setProcessStatusSelection(processStatusSelectedArray);
  // }, [
  //   processInstanceFilters,
  //   dateParametersToAlwaysFilterBy,
  //   parametersToGetFromSearchParams,
  //   processModelAvailableItems,
  // ]);

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
      return (reportMetadata as any).columns;
    }
    return null;
  };

  const reportFilterBy = () => {
    return (reportMetadata as any).filter_by;
  };

  const navigateToNewReport = (queryParamString: string) => {
    removeError();
    setProcessInstanceReportJustSaved(null);
    setProcessInstanceFilters({});
    navigate(`${processInstanceListPathPrefix}?${queryParamString}`);
  };

  const addFieldValueToReportMetadata = (
    postBody: ReportMetadata,
    fieldName: string,
    fieldValue: string
  ) => {
    if (fieldValue) {
      postBody.filter_by.push({
        field_name: fieldName,
        field_value: fieldValue,
      });
    }
  };

  const applyFilter = (event: any) => {
    event.preventDefault();
    setProcessInitiatorNotFoundErrorText('');

    const { page, perPage } = getPageInfoFromSearchParams(
      searchParams,
      undefined,
      undefined,
      paginationQueryParamPrefix
    );
    // let queryParamString = `per_page=${perPage}&page=${page}&user_filter=true`;
    const queryParamString = `per_page=${perPage}&page=${page}`;
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

    const postBody: ReportMetadata = {
      columns: [],
      filter_by: [],
      order_by: [],
    };

    addFieldValueToReportMetadata(postBody, 'start_from', startFromSeconds);
    addFieldValueToReportMetadata(postBody, 'start_to', startToSeconds);
    addFieldValueToReportMetadata(postBody, 'end_from', endFromSeconds);
    addFieldValueToReportMetadata(postBody, 'end_to', endToSeconds);
    if (processStatusSelection.length > 0) {
      addFieldValueToReportMetadata(
        postBody,
        'process_status',
        processStatusSelection.join(',')
      );
    }

    if (processModelSelection) {
      addFieldValueToReportMetadata(
        postBody,
        'process_model_identifier',
        processModelSelection.id
      );
    }

    if (processInstanceReportSelection) {
      addFieldValueToReportMetadata(
        postBody,
        'report_id',
        processInstanceReportSelection.id.toString()
      );
    }

    postBody.columns = reportColumns();

    if (processInitiatorSelection) {
      addFieldValueToReportMetadata(
        postBody,
        'process_initiator_username',
        processInitiatorSelection.username
      );
      // navigateToNewReport(queryParamString);
    }
    // } else if (processInitiatorText) {
    // HttpService.makeCallToBackend({
    //   path: targetUris.userExists,
    //   httpMethod: 'POST',
    //   postBody: { username: processInitiatorText },
    //   successCallback: (result: any) => {
    //     if (result.user_found) {
    //       queryParamString += `&process_initiator_username=${processInitiatorText}`;
    //       // navigateToNewReport(queryParamString);
    //     } else {
    //       setProcessInitiatorNotFoundErrorText(
    //         `The provided username is invalid. Please type the exact username.`
    //       );
    //     }
    //   },
    // });
    // } else {
    //   navigateToNewReport(queryParamString);
    // }

    // http://localhost:7001/admin/process-instances/for-me?per_page=50&page=1&report_metadata_base64=eyJjb2x1bW5zIjpudWxsLCJmaWx0ZXJfYnkiOlt7ImZpZWxkX25hbWUiOiJwcm9jZXNzX3N0YXR1cyIsImZpZWxkX3ZhbHVlIjoiY29tcGxldGUifV0sIm9yZGVyX2J5IjpbXX0%3D
    // const queryParamString = `per_page=${perPage}&page=${page}`;

    setListHasBeenFiltered(true);
    searchParams.set('per_page', perPage.toString());
    searchParams.set('page', page.toString());

    // const reportMetadataBase64 = encodeBase64(JSON.stringify(postBody));
    // searchParams.set('report_metadata_base64', reportMetadataBase64);
    setSearchParams(searchParams);

    HttpService.makeCallToBackend({
      path: `${processInstanceApiSearchPath}?${queryParamString}`,
      httpMethod: 'POST',
      postBody: { report_metadata: postBody },
      failureCallback: stopRefreshing,
      onUnauthorized: stopRefreshing,
      successCallback: (result: any) => {
        setProcessInstancesFromResult(result);
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
    return capitalizeFirstLetter((value || '').replaceAll('_', ' '));
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
    setProcessInitiatorSelection(null);
    setProcessInitiatorText('');
    setRequiresRefilter(true);
    if (reportMetadata) {
      reportMetadata.filter_by = [];
    }
  };

  const processInstanceReportDidChange = (selection: any, mode?: string) => {
    clearFilters();
    const selectedReport = selection.selectedItem;
    setProcessInstanceReportSelection(selectedReport);

    let queryParamString = '';
    if (selectedReport) {
      queryParamString = `?report_id=${selectedReport.id}`;
    }

    removeError();
    setProcessInstanceReportJustSaved(mode || null);
    navigate(`${processInstanceListPathPrefix}${queryParamString}`);
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
    } = calculateStartAndEndSeconds(false);

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
        processInitiatorSelection={processInitiatorSelection}
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
      setRequiresRefilter(true);
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
      reportColumnForEditing.filter_field_value =
        reportFilter.field_value || '';
      reportColumnForEditing.filter_operator =
        reportFilter.operator || 'equals';
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
                          return processInstanceInitatorOption.username;
                        }
                        return null;
                      }}
                      placeholder="Start typing username"
                      titleText="Started By"
                      selectedItem={processInitiatorSelection}
                    />
                  );
                }
                return (
                  <TextInput
                    id="process-instance-initiator-search"
                    placeholder="Enter username"
                    labelText="Started By"
                    invalid={processInitiatorNotFoundErrorText !== ''}
                    invalidText={processInitiatorNotFoundErrorText}
                    onChange={(event: any) => {
                      setProcessInitiatorText(event.target.value);
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
          <Column sm={4} md={4} lg={8}>
            {saveAsReportComponent()}
            {deleteReportComponent()}
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

  const formattedColumn = (row: any, column: any) => {
    const reportColumnFormatters: Record<string, any> = {
      id: formatProcessInstanceId,
      process_model_identifier: formatProcessModelIdentifier,
      process_model_display_name: formatProcessModelDisplayName,
      status: formatProcessInstanceStatus,
      start_in_seconds: formatSecondsForDisplay,
      end_in_seconds: formatSecondsForDisplay,
      updated_at_in_seconds: formatSecondsForDisplay,
    };
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
    if (column.accessor === 'process_model_display_name') {
      return <td> {formatter(row, value)} </td>;
    }
    if (column.accessor === 'waiting_for') {
      return <td> {getWaitingForTableCellComponent(row)} </td>;
    }
    if (column.accessor === 'updated_at_in_seconds') {
      return (
        <TableCellWithTimeAgoInWords
          timeInSeconds={row.updated_at_in_seconds}
        />
      );
    }
    return (
      // eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions
      <td data-qa={`process-instance-show-link-${column.accessor}`}>
        {formatter(row, value)}
      </td>
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
      process_initiator_username: 'Started By',
    };
    const getHeaderLabel = (header: string) => {
      return headerLabels[header] ?? header;
    };
    const headers = reportColumns().map((column: any) => {
      return getHeaderLabel((column as any).Header);
    });
    if (showActionsColumn) {
      headers.push('Action');
    }

    const rows = processInstances.map((row: any) => {
      const currentRow = reportColumns().map((column: any) => {
        return formattedColumn(row, column);
      });
      if (showActionsColumn) {
        let buttonElement = null;
        const interstitialUrl = `/process/${modifyProcessIdentifierForPathParam(
          row.process_model_identifier
        )}/${row.id}/interstitial`;
        const regex = new RegExp(`\\b(${preferredUsername}|${userEmail})\\b`);
        let hasAccessToCompleteTask = false;
        if (
          canCompleteAllTasks ||
          (row.potential_owner_usernames || '').match(regex)
        ) {
          hasAccessToCompleteTask = true;
        }

        buttonElement = (
          <Button
            kind={
              hasAccessToCompleteTask && row.task_id ? 'secondary' : 'tertiary'
            }
            href={interstitialUrl}
          >
            Go
          </Button>
        );
        currentRow.push(<td>{buttonElement}</td>);
      }

      const rowStyle = { cursor: 'pointer' };
      const modifiedModelId = modifyProcessIdentifierForPathParam(
        row.process_model_identifier
      );
      const navigateToProcessInstance = () => {
        navigate(
          `${processInstanceShowPathPrefix}/${modifiedModelId}/${row.id}`
        );
      };
      return (
        // eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions
        <tr
          style={rowStyle}
          key={row.id}
          onClick={navigateToProcessInstance}
          onKeyDown={navigateToProcessInstance}
        >
          {currentRow}
        </tr>
      );
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
      {processInstanceReportSaveTag()}
      <Filters
        filterOptions={filterOptions}
        showFilterOptions={showFilterOptions}
        setShowFilterOptions={setShowFilterOptions}
        reportSearchComponent={reportSearchComponent}
        filtersEnabled={filtersEnabled}
      />
      {resultsTable}
    </>
  );
}
