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
  // TableHeader,
  // TableHead,
  // TableRow,
  // TableBody,
  // TableCell,
  // @ts-ignore
} from '@carbon/react';
import { PROCESS_STATUSES, DATE_FORMAT, DATE_FORMAT_CARBON } from '../config';
import {
  convertDateStringToSeconds,
  convertSecondsToFormattedDate,
  getPageInfoFromSearchParams,
  getProcessModelFullIdentifierFromSearchParams,
} from '../helpers';

import PaginationForTable from '../components/PaginationForTable';
import 'react-datepicker/dist/react-datepicker.css';

import ErrorContext from '../contexts/ErrorContext';
import HttpService from '../services/HttpService';

import 'react-bootstrap-typeahead/css/Typeahead.css';
import 'react-bootstrap-typeahead/css/Typeahead.bs5.css';
import { PaginationObject, ProcessModel } from '../interfaces';
import ProcessModelSearch from '../components/ProcessModelSearch';

export default function ProcessInstanceList() {
  const params = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [processInstances, setProcessInstances] = useState([]);
  const [reportMetadata, setReportMetadata] = useState({});
  const [pagination, setPagination] = useState<PaginationObject | null>(null);

  const oneHourInSeconds = 3600;
  const oneMonthInSeconds = oneHourInSeconds * 24 * 30;
  const [startFrom, setStartFrom] = useState<string>('');
  const [startTo, setStartTo] = useState<string>('');
  const [endFrom, setEndFrom] = useState<string>('');
  const [endTo, setEndTo] = useState<string>('');
  const [showFilterOptions, setShowFilterOptions] = useState<boolean>(false);

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

  const parametersToAlwaysFilterBy = useMemo(() => {
    return {
      start_from: setStartFrom,
      start_to: setStartTo,
      end_from: setEndFrom,
      end_to: setEndTo,
    };
  }, [setStartFrom, setStartTo, setEndFrom, setEndTo]);

  const parametersToGetFromSearchParams = useMemo(() => {
    return {
      process_group_identifier: null,
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
    }
    function getProcessInstances() {
      const { page, perPage } = getPageInfoFromSearchParams(searchParams);
      let queryParamString = `per_page=${perPage}&page=${page}`;

      Object.keys(parametersToAlwaysFilterBy).forEach((paramName: string) => {
        // @ts-expect-error TS(7053) FIXME:
        const functionToCall = parametersToAlwaysFilterBy[paramName];
        const searchParamValue = searchParams.get(paramName);
        if (searchParamValue) {
          queryParamString += `&${paramName}=${searchParamValue}`;
          const dateString = convertSecondsToFormattedDate(
            searchParamValue as any
          );
          functionToCall(dateString);
        }
      });

      Object.keys(parametersToGetFromSearchParams).forEach(
        (paramName: string) => {
          if (searchParams.get(paramName)) {
            // @ts-expect-error TS(7053) FIXME:
            const functionToCall = parametersToGetFromSearchParams[paramName];
            queryParamString += `&${paramName}=${searchParams.get(paramName)}`;
            if (functionToCall !== null) {
              functionToCall(searchParams.get(paramName) || '');
            }
          }
        }
      );
      HttpService.makeCallToBackend({
        path: `/process-instances?${queryParamString}`,
        successCallback: setProcessInstancesFromResult,
      });
    }
    function processResultForProcessModels(result: any) {
      const processModelFullIdentifier =
        getProcessModelFullIdentifierFromSearchParams(searchParams);
      const selectionArray = result.results.map((item: any) => {
        const label = `${item.process_group_id}/${item.id}`;
        Object.assign(item, { label });
        if (label === processModelFullIdentifier) {
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

    HttpService.makeCallToBackend({
      path: `/process-models?per_page=1000`,
      successCallback: processResultForProcessModels,
    });
  }, [
    searchParams,
    params,
    oneMonthInSeconds,
    oneHourInSeconds,
    parametersToAlwaysFilterBy,
    parametersToGetFromSearchParams,
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
    const { page, perPage } = getPageInfoFromSearchParams(searchParams);
    let queryParamString = `per_page=${perPage}&page=${page}`;

    const startFromSeconds = convertDateStringToSeconds(startFrom);
    const endFromSeconds = convertDateStringToSeconds(endFrom);
    const startToSeconds = convertDateStringToSeconds(startTo);
    const endToSeconds = convertDateStringToSeconds(endTo);
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
      queryParamString += `&process_group_identifier=${processModelSelection.process_group_id}&process_model_identifier=${processModelSelection.id}`;
    }

    setErrorMessage(null);
    navigate(`/admin/process-instances?${queryParamString}`);
  };

  const dateComponent = (
    labelString: any,
    name: any,
    initialDate: any,
    onChangeFunction: any
  ) => {
    return (
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
            onChangeFunction(dateChangeEvent.srcElement.value);
          }}
          value={initialDate}
        />
      </DatePicker>
    );
  };

  const getSearchParamsAsQueryString = () => {
    let queryParamString = '';
    Object.keys(parametersToAlwaysFilterBy).forEach((paramName) => {
      const searchParamValue = searchParams.get(paramName);
      if (searchParamValue) {
        queryParamString += `&${paramName}=${searchParamValue}`;
      }
    });

    Object.keys(parametersToGetFromSearchParams).forEach(
      (paramName: string) => {
        if (searchParams.get(paramName)) {
          queryParamString += `&${paramName}=${searchParams.get(paramName)}`;
        }
      }
    );
    return queryParamString;
  };

  const processStatusSearch = () => {
    return (
      <MultiSelect
        label="Choose Status"
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
    setStartFrom('');
    setStartTo('');
    setEndFrom('');
    setEndTo('');
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
              startFrom,
              setStartFrom
            )}
          </Column>
          <Column md={4}>
            {dateComponent('Start date to', 'start-to', startTo, setStartTo)}
          </Column>
          <Column md={4}>
            {dateComponent('End date from', 'end-from', endFrom, setEndFrom)}
          </Column>
          <Column md={4}>
            {dateComponent('End date to', 'end-to', endTo, setEndTo)}
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
              <Button kind="secondary" onClick={applyFilter}>
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
      id: 'Process Instance Id',
      process_group_identifier: 'Process Group',
      process_model_indetifier: 'Process Model',
      start_in_seconds: 'Start Time',
      end_in_seconds: 'End Time',
      status: 'Status',
    };
    const getHeaderLabel = (header: string) => {
      return headerLabels[header] ?? header;
    };
    const headers = (reportMetadata as any).columns.map((column: any) => {
      return <th>{getHeaderLabel((column as any).Header)}</th>;
    });

    const formatProcessInstanceId = (row: any, id: any) => {
      return (
        <Link
          data-qa="process-instance-show-link"
          to={`/admin/process-models/${row.process_group_identifier}/${row.process_model_identifier}/process-instances/${row.id}`}
        >
          {id}
        </Link>
      );
    };
    const formatProcessGroupIdentifier = (row: any, identifier: any) => {
      return (
        <Link to={`/admin/process-groups/${identifier}`}>{identifier}</Link>
      );
    };
    const formatProcessModelIdentifier = (row: any, identifier: any) => {
      return (
        <Link
          to={`/admin/process-models/${row.process_group_identifier}/${identifier}`}
        >
          {identifier}
        </Link>
      );
    };
    const formatSecondsForDisplay = (row: any, seconds: any) => {
      return convertSecondsToFormattedDate(seconds) || '-';
    };
    const defaultFormatter = (row: any, value: any) => {
      return value;
    };

    const columnFormatters: Record<string, any> = {
      id: formatProcessInstanceId,
      process_group_identifier: formatProcessGroupIdentifier,
      process_model_identifier: formatProcessModelIdentifier,
      start_in_seconds: formatSecondsForDisplay,
      end_in_seconds: formatSecondsForDisplay,
    };
    const formattedColumn = (row: any, column: any) => {
      const formatter = columnFormatters[column.accessor] ?? defaultFormatter;
      const value = row[column.accessor];
      return <td>{formatter(row, value)}</td>;
    }

    const rows = processInstances.map((row) => {
      const currentRow = (reportMetadata as any).columns.map((column: any) => {
        return formattedColumn(row, column);
      });
      return <tr key={(row as any).id}>{currentRow}</tr>;
    });
    return (
      <Table size="lg">
        <thead>
          <tr>{headers}</tr>
        </thead>
        <tbody>{rows}</tbody>
      </Table>
    );
  };

  const processInstanceTitleElement = () => {
    const processModelFullIdentifier =
      getProcessModelFullIdentifierFromSearchParams(searchParams);
    if (processModelFullIdentifier === null) {
      return <h2>Process Instances</h2>;
    }
    return (
      <h2>
        Process Instances for:{' '}
        <Link to={`/admin/process-models/${processModelFullIdentifier}`}>
          {processModelFullIdentifier}
        </Link>
      </h2>
    );
  };

  const toggleShowFilterOptions = () => {
    setShowFilterOptions(!showFilterOptions);
  };

  if (pagination) {
    const { page, perPage } = getPageInfoFromSearchParams(searchParams);
    return (
      <>
        {processInstanceTitleElement()}
        <Grid fullWidth>
          <Column lg={15} />
          <Column lg={1}>
            <Button
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
        <br />
        <Grid fullWidth>
          <Column lg={16}>
            <PaginationForTable
              page={page}
              perPage={perPage}
              pagination={pagination}
              tableToDisplay={buildTable()}
              queryParamString={getSearchParamsAsQueryString()}
              path="/admin/process-instances"
            />
          </Column>
        </Grid>
      </>
    );
  }

  return null;
}
