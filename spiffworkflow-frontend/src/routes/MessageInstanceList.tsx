import { useEffect, useState } from 'react';
import { Table } from 'react-bootstrap';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import PaginationForTable from '../components/PaginationForTable';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import {
  convertSecondsToFormattedDate,
  getPageInfoFromSearchParams,
} from '../helpers';
import HttpService from '../services/HttpService';

export default function MessageInstanceList() {
  const params = useParams();
  const [searchParams] = useSearchParams();
  const [messageIntances, setMessageInstances] = useState([]);
  const [pagination, setPagination] = useState(null);

  useEffect(() => {
    const setMessageInstanceListFromResult = (result: any) => {
      setMessageInstances(result.results);
      setPagination(result.pagination);
    };
    const { page, perPage } = getPageInfoFromSearchParams(searchParams);
    let queryParamString = `per_page=${perPage}&page=${page}`;
    if (searchParams.get('process_instance_id')) {
      queryParamString += `&process_instance_id=${searchParams.get(
        'process_instance_id'
      )}`;
    }
    HttpService.makeCallToBackend({
      path: `/messages?${queryParamString}`,
      successCallback: setMessageInstanceListFromResult,
    });
  }, [searchParams, params]);

  const buildTable = () => {
    // return null;
    const rows = messageIntances.map((row) => {
      const rowToUse = row as any;
      return (
        <tr key={rowToUse.id}>
          <td>{rowToUse.id}</td>
          <td>
            <Link
              data-qa="process-model-show-link"
              to={`/admin/process-groups/${rowToUse.process_group_identifier}`}
            >
              {rowToUse.process_group_identifier}
            </Link>
          </td>
          <td>
            <Link
              data-qa="process-model-show-link"
              to={`/admin/process-models/${rowToUse.process_group_identifier}/${rowToUse.process_model_identifier}`}
            >
              {rowToUse.process_model_identifier}
            </Link>
          </td>
          <td>
            <Link
              data-qa="process-instance-show-link"
              to={`/admin/process-models/${rowToUse.process_group_identifier}/${rowToUse.process_model_identifier}/process-instances/${rowToUse.process_instance_id}`}
            >
              {rowToUse.process_instance_id}
            </Link>
          </td>
          <td>{rowToUse.message_identifier}</td>
          <td>{rowToUse.message_type}</td>
          <td>{rowToUse.failure_cause}</td>
          <td>{rowToUse.status}</td>
          <td>
            {convertSecondsToFormattedDate(rowToUse.created_at_in_seconds)}
          </td>
        </tr>
      );
    });
    return (
      <Table striped bordered>
        <thead>
          <tr>
            <th>Instance Id</th>
            <th>Process Group</th>
            <th>Process Model</th>
            <th>Process Instance</th>
            <th>Message Model</th>
            <th>Type</th>
            <th>Failure Cause</th>
            <th>Status</th>
            <th>Created At</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </Table>
    );
  };

  if (pagination) {
    const { page, perPage } = getPageInfoFromSearchParams(searchParams);
    let queryParamString = '';
    let breadcrumbElement = null;
    if (searchParams.get('process_instance_id')) {
      queryParamString += `&process_group_id=${searchParams.get(
        'process_group_id'
      )}&process_model_id=${searchParams.get(
        'process_model_id'
      )}&process_instance_id=${searchParams.get('process_instance_id')}`;
      breadcrumbElement = (
        <ProcessBreadcrumb
          processModelId={searchParams.get('process_model_id') as any}
          processGroupId={searchParams.get('process_group_id') as any}
          linkProcessModel
        />
      );
    }
    return (
      <>
        {breadcrumbElement}
        <h2>Messages</h2>
        <PaginationForTable
          page={page}
          perPage={perPage}
          pagination={pagination}
          tableToDisplay={buildTable()}
          queryParamString={queryParamString}
          path="/admin/messages"
        />
      </>
    );
  }
  return null;
}
