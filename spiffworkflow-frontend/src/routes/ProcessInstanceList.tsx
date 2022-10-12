import { useContext, useEffect, useMemo, useState } from 'react';
import {
  Link,
  useNavigate,
  useParams,
  useSearchParams,
} from 'react-router-dom';

import { Button, Table, Stack, Form, InputGroup } from 'react-bootstrap';
// @ts-expect-error TS(7016) FIXME: Could not find a declaration file for module 'reac... Remove this comment to see the full error message
import DatePicker from 'react-datepicker';
import { Typeahead } from 'react-bootstrap-typeahead';
import { Option } from 'react-bootstrap-typeahead/types/types';
import { PROCESS_STATUSES, DATE_FORMAT } from '../config';
import {
  convertDateToSeconds,
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

export default function ProcessInstanceList() {
  const params = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [processInstances, setProcessInstances] = useState([]);
  const [pagination, setPagination] = useState(null);

  const oneHourInSeconds = 3600;
  const oneMonthInSeconds = oneHourInSeconds * 24 * 30;
  const [startFrom, setStartFrom] = useState(null);
  const [startTill, setStartTill] = useState(null);
  const [endFrom, setEndFrom] = useState(null);
  const [endTill, setEndTill] = useState(null);

  const setErrorMessage = (useContext as any)(ErrorContext)[1];

  const [processStatuseSelectionOptions, setProcessStatusSelectionOptions] =
    useState<any[]>([]);
  const [processStatusSelection, setProcessStatusSelection] = useState<
    Option[]
  >([]);
  const [processModeleSelectionOptions, setProcessModelSelectionOptions] =
    useState([]);
  const [processModelSelection, setProcessModelSelection] = useState<Option[]>(
    []
  );

  const parametersToAlwaysFilterBy = useMemo(() => {
    return {
      start_from: setStartFrom,
      start_till: setStartTill,
      end_from: setEndFrom,
      end_till: setEndTill,
    };
  }, [setStartFrom, setStartTill, setEndFrom, setEndTill]);

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
          functionToCall(searchParamValue);
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
          setProcessModelSelection([item]);
        }
        return item;
      });
      setProcessModelSelectionOptions(selectionArray);

      const processStatusSelectedArray: Option[] = [];
      const processStatusSelectionArray = PROCESS_STATUSES.map(
        (processStatusOption: any) => {
          const regex = new RegExp(`\\b${processStatusOption}\\b`);
          if ((searchParams.get('process_status') || '').match(regex)) {
            processStatusSelectedArray.push({ label: processStatusOption });
          }
          return { label: processStatusOption };
        }
      );
      setProcessStatusSelection(processStatusSelectedArray);
      setProcessStatusSelectionOptions(processStatusSelectionArray);

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

  const handleFilter = (event: any) => {
    event.preventDefault();
    const { page, perPage } = getPageInfoFromSearchParams(searchParams);
    let queryParamString = `per_page=${perPage}&page=${page}`;

    if (isTrueComparison(startFrom, '>', startTill)) {
      setErrorMessage('startFrom cannot be after startTill');
      return;
    }
    if (isTrueComparison(endFrom, '>', endTill)) {
      setErrorMessage('endFrom cannot be after endTill');
      return;
    }
    if (isTrueComparison(startFrom, '>', endFrom)) {
      setErrorMessage('startFrom cannot be after endFrom');
      return;
    }
    if (isTrueComparison(startTill, '>', endTill)) {
      setErrorMessage('startTill cannot be after endTill');
      return;
    }

    if (startFrom) {
      queryParamString += `&start_from=${startFrom}`;
    }
    if (startTill) {
      queryParamString += `&start_till=${startTill}`;
    }
    if (endFrom) {
      queryParamString += `&end_from=${endFrom}`;
    }
    if (endTill) {
      queryParamString += `&end_till=${endTill}`;
    }
    if (processStatusSelection.length > 0) {
      const processStatusSelectionString = processStatusSelection.map(
        (pss: any) => {
          return pss.label;
        }
      );
      queryParamString += `&process_status=${processStatusSelectionString}`;
    }
    if (processModelSelection.length > 0) {
      const currentProcessModel: any = processModelSelection[0];
      queryParamString += `&process_group_identifier=${currentProcessModel.process_group_id}&process_model_identifier=${currentProcessModel.id}`;
    }

    setErrorMessage('');
    navigate(`/admin/process-instances?${queryParamString}`);
  };

  const dateComponent = (
    labelString: any,
    name: any,
    initialDate: any,
    onChangeFunction: any
  ) => {
    let selectedDate = null;
    if (initialDate) {
      selectedDate = new Date(initialDate * 1000);
    }
    return (
      <Form.Group>
        <InputGroup>
          <Stack className="ms-auto" direction="horizontal" gap={3}>
            <InputGroup.Text className="text-nowrap">
              {labelString}
              {'\u00A0'}
            </InputGroup.Text>
            <DatePicker
              id={`date-picker-${name}`}
              selected={selectedDate}
              onChange={(date: any) =>
                convertDateToSeconds(date, onChangeFunction)
              }
              showTimeSelect
              dateFormat={DATE_FORMAT}
            />
          </Stack>
        </InputGroup>
      </Form.Group>
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

  const processModelSearch = () => {
    return (
      <Form.Group>
        <InputGroup>
          <InputGroup.Text className="text-nowrap">
            Process Model:{' '}
          </InputGroup.Text>
          <Typeahead
            style={{ width: 500 }}
            id="process-model-selection"
            labelKey="label"
            onChange={setProcessModelSelection}
            options={processModeleSelectionOptions}
            placeholder="Choose a process model..."
            selected={processModelSelection}
          />
        </InputGroup>
      </Form.Group>
    );
  };

  const processStatusSearch = () => {
    return (
      <Form.Group>
        <InputGroup>
          <InputGroup.Text className="text-nowrap">
            Process Status:{' '}
          </InputGroup.Text>
          <Typeahead
            multiple
            style={{ width: 500 }}
            id="process-status-selection"
            // for cypress tests since data-qa does not work
            inputProps={{
              name: 'process-status-selection',
            }}
            labelKey="label"
            onChange={setProcessStatusSelection}
            options={processStatuseSelectionOptions}
            placeholder="Choose process statuses..."
            selected={processStatusSelection}
          />
        </InputGroup>
      </Form.Group>
    );
  };

  const filterOptions = () => {
    return (
      <div className="container">
        <div className="row">
          <div className="col">
            <form onSubmit={handleFilter}>
              <Stack direction="horizontal" gap={3}>
                {processModelSearch()}
              </Stack>
              <br />
              <Stack direction="horizontal" gap={3}>
                {dateComponent(
                  'Start Range: ',
                  'start-from',
                  startFrom,
                  setStartFrom
                )}
                {dateComponent('-', 'start-till', startTill, setStartTill)}
              </Stack>
              <br />
              <Stack direction="horizontal" gap={3}>
                {dateComponent(
                  'End Range: \u00A0\u00A0',
                  'end-from',
                  endFrom,
                  setEndFrom
                )}
                {dateComponent('-', 'end-till', endTill, setEndTill)}
              </Stack>
              <br />
              <Stack direction="horizontal" gap={3}>
                {processStatusSearch()}
              </Stack>
              <Stack direction="horizontal" gap={3}>
                <Button className="ms-auto" variant="secondary" type="submit">
                  Filter
                </Button>
              </Stack>
            </form>
          </div>
          <div className="col" />
        </div>
      </div>
    );
  };

  const buildTable = () => {
    const rows = processInstances.map((row: any) => {
      const formattedStartDate =
        convertSecondsToFormattedDate(row.start_in_seconds) || '-';
      const formattedEndDate =
        convertSecondsToFormattedDate(row.end_in_seconds) || '-';

      return (
        <tr key={row.id}>
          <td>
            <Link
              data-qa="process-instance-show-link"
              to={`/admin/process-models/${row.process_group_identifier}/${row.process_model_identifier}/process-instances/${row.id}`}
            >
              {row.id}
            </Link>
          </td>
          <td>
            <Link to={`/admin/process-groups/${row.process_group_identifier}`}>
              {row.process_group_identifier}
            </Link>
          </td>
          <td>
            <Link
              to={`/admin/process-models/${row.process_group_identifier}/${row.process_model_identifier}`}
            >
              {row.process_model_identifier}
            </Link>
          </td>
          <td>{formattedStartDate}</td>
          <td>{formattedEndDate}</td>
          <td data-qa={`process-instance-status-${row.status}`}>
            {row.status}
          </td>
        </tr>
      );
    });
    return (
      <Table striped bordered>
        <thead>
          <tr>
            <th>Process Instance Id</th>
            <th>Process Group</th>
            <th>Process Model</th>
            <th>Start Time</th>
            <th>End Time</th>
            <th>Status</th>
          </tr>
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

  if (pagination) {
    const { page, perPage } = getPageInfoFromSearchParams(searchParams);
    return (
      <>
        {processInstanceTitleElement()}
        {filterOptions()}
        <PaginationForTable
          page={page}
          perPage={perPage}
          pagination={pagination}
          tableToDisplay={buildTable()}
          queryParamString={getSearchParamsAsQueryString()}
          path="/admin/process-instances"
        />
      </>
    );
  }

  return null;
}
