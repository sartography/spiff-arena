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
  // @ts-ignore
} from '@carbon/react';
import { PROCESS_STATUSES, DATE_FORMAT, DATE_FORMAT_CARBON } from '../config';
import {
  convertDateStringToSeconds,
  convertSecondsToFormattedDate,
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
import ProcessBreadcrumb from './ProcessBreadcrumb';

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
          setShowFilterOptions(true);
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
      const processModelFullIdentifier =
        getProcessModelFullIdentifierFromSearchParams(searchParams);
      const selectionArray = result.results.map((item: any) => {
        const label = `${item.id}`;
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

    // populate process model selection
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
      queryParamString += `&process_model_identifier=${processModelSelection.id}`;
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
      id: 'Process Instance Id',
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
      return convertSecondsToFormattedDate(seconds) || '-';
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
              <TableHeader key={header}>{header}</TableHeader>
            ))}
          </TableRow>
        </TableHead>
        <tbody>{rows}</tbody>
      </Table>
    );
  };

  const processInstanceBreadcrumbElement = () => {
    const processModelFullIdentifier =
      getProcessModelFullIdentifierFromSearchParams(searchParams);
    if (processModelFullIdentifier === null) {
      return null;
    }

    return (
      <ProcessBreadcrumb
        hotCrumbs={[
          ['Process Groups', '/admin'],
          [
            `Process Model: ${processModelFullIdentifier}`,
            `process_model:${processModelFullIdentifier}:link`,
          ],
          ['Process Instances'],
        ]}
      />
    );
  };

  const processInstanceTitleElement = () => {
    return <h1>Process Instances</h1>;
  };

  const toggleShowFilterOptions = () => {
    setShowFilterOptions(!showFilterOptions);
  };

  if (pagination) {
    const { page, perPage } = getPageInfoFromSearchParams(searchParams);
    return (
      <>
        {processInstanceBreadcrumbElement()}
        {processInstanceTitleElement()}
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
        <br />
        <PaginationForTable
          page={page}
          perPage={perPage}
          pagination={pagination}
          tableToDisplay={buildTable()}
          queryParamString={getSearchParamsAsQueryString()}
        />
      </>
    );
  }

  return null;
}
