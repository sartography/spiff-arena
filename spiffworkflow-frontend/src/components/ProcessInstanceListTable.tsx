import { useContext, useEffect, useMemo, useState } from 'react';
import {
  Link,
  useNavigate,
  useParams,
  useSearchParams,
} from 'react-router-dom';

// @ts-ignore
import { Filter } from '@carbon/icons-react';
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
  modifyProcessModelPath,
} from '../helpers';

import PaginationForTable from './PaginationForTable';
import 'react-datepicker/dist/react-datepicker.css';

import ErrorContext from '../contexts/ErrorContext';
import HttpService from '../services/HttpService';

import 'react-bootstrap-typeahead/css/Typeahead.css';
import 'react-bootstrap-typeahead/css/Typeahead.bs5.css';
import { PaginationObject, ProcessModel } from '../interfaces';
import ProcessModelSearch from './ProcessModelSearch';

type OwnProps = {
  filtersEnabled?: boolean;
  processModelFullIdentifier?: string;
  paginationQueryParamPrefix?: string;
  perPageOptions?: number[];
};

interface dateParameters {
  [key: string]: ((..._args: any[]) => any)[];
}

export default function ProcessInstanceListTable({
  filtersEnabled = true,
  processModelFullIdentifier,
  paginationQueryParamPrefix,
  perPageOptions,
}: OwnProps) {
  const params = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [processInstances, setProcessInstances] = useState([]);
  const [reportMetadata, setReportMetadata] = useState({});
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
      setReportMetadata(result.report_metadata);
      setPagination(result.pagination);
      setProcessInstanceFilters(result.filters);
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

    if (filtersEnabled) {
      // populate process model selection
      HttpService.makeCallToBackend({
        path: `/process-models?per_page=1000&recursive=true`,
        successCallback: processResultForProcessModels,
      });
    } else {
      getProcessInstances();
    }
  }, [
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

  const applyFilter = (event: any) => {
    event.preventDefault();
    const { page, perPage } = getPageInfoFromSearchParams(
      searchParams,
      undefined,
      undefined,
      paginationQueryParamPrefix
    );
    let queryParamString = `per_page=${perPage}&page=${page}&user_filter=true`;

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
    if (isTrueComparison(startFromSeconds, '>', startToSeconds)) {
      setErrorMessage({
        message: '"Start date from" cannot be after "start date to"',
      });
      return;
    }
    if (isTrueComparison(endFromSeconds, '>', endToSeconds)) {
      setErrorMessage({
        message: '"End date from" cannot be after "end date to"',
      });
      return;
    }
    if (isTrueComparison(startFromSeconds, '>', endFromSeconds)) {
      setErrorMessage({
        message: '"Start date from" cannot be after "end date from"',
      });
      return;
    }
    if (isTrueComparison(startToSeconds, '>', endToSeconds)) {
      setErrorMessage({
        message: '"Start date to" cannot be after "end date to"',
      });
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

    setErrorMessage(null);
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

  const filterOptions = () => {
    if (!showFilterOptions) {
      return null;
    }
    return (
      <>
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
          <Column md={4}>
            <ButtonSet>
              <Button
                kind=""
                className="button-white-background"
                onClick={clearFilters}
              >
                Clear
              </Button>
              <Button
                kind="secondary"
                onClick={applyFilter}
                data-qa="filter-button"
              >
                Filter
              </Button>
            </ButtonSet>
          </Column>
        </Grid>
      </>
    );
  };

  const buildTable = () => {
    const headerLabels: Record<string, string> = {
      id: 'Id',
      process_model_identifier: 'Process Model',
      start_in_seconds: 'Start Time',
      end_in_seconds: 'End Time',
      status: 'Status',
      spiff_step: 'SpiffWorkflow Step',
    };
    const getHeaderLabel = (header: string) => {
      return headerLabels[header] ?? header;
    };
    const headers = (reportMetadata as any).columns.map((column: any) => {
      // return <th>{getHeaderLabel((column as any).Header)}</th>;
      return getHeaderLabel((column as any).Header);
    });

    const formatProcessInstanceId = (row: any, id: any) => {
      const modifiedProcessModelId: String = modifyProcessModelPath(
        row.process_model_identifier
      );
      return (
        <Link
          data-qa="process-instance-show-link"
          to={`/admin/process-models/${modifiedProcessModelId}/process-instances/${row.id}`}
        >
          {id}
        </Link>
      );
    };
    const formatProcessModelIdentifier = (_row: any, identifier: any) => {
      return (
        <Link
          to={`/admin/process-models/${modifyProcessModelPath(identifier)}`}
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

    const columnFormatters: Record<string, any> = {
      id: formatProcessInstanceId,
      process_model_identifier: formatProcessModelIdentifier,
      start_in_seconds: formatSecondsForDisplay,
      end_in_seconds: formatSecondsForDisplay,
    };
    const formattedColumn = (row: any, column: any) => {
      const formatter = columnFormatters[column.accessor] ?? defaultFormatter;
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
      const currentRow = (reportMetadata as any).columns.map((column: any) => {
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

  const filterComponent = () => {
    if (!filtersEnabled) {
      return null;
    }
    return (
      <>
        <Grid fullWidth>
          <Column
            sm={{ span: 1, offset: 3 }}
            md={{ span: 1, offset: 7 }}
            lg={{ span: 1, offset: 15 }}
          >
            <Button
              data-qa="filter-section-expand-toggle"
              kind="ghost"
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

  if (pagination) {
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
        {filterComponent()}
        <PaginationForTable
          page={page}
          perPage={perPage}
          pagination={pagination}
          tableToDisplay={buildTable()}
          paginationQueryParamPrefix={paginationQueryParamPrefix}
          perPageOptions={perPageOptions}
        />
      </>
    );
  }

  return null;
}
