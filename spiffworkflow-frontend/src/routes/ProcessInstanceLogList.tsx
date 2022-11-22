import { useEffect, useState } from 'react';
// @ts-ignore
import { Table } from '@carbon/react';
import { useParams, useSearchParams, Link } from 'react-router-dom';
import PaginationForTable from '../components/PaginationForTable';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import {
  getPageInfoFromSearchParams,
  modifyProcessIdentifierForPathParam,
  unModifyProcessIdentifierForPathParam,
  convertSecondsToFormattedDateTime,
} from '../helpers';
import HttpService from '../services/HttpService';

export default function ProcessInstanceLogList() {
  const params = useParams();
  const [searchParams] = useSearchParams();
  const [processInstanceLogs, setProcessInstanceLogs] = useState([]);
  const [pagination, setPagination] = useState(null);
  const modifiedProcessModelId = modifyProcessIdentifierForPathParam(
    `${params.process_model_id}`
  );

  useEffect(() => {
    const setProcessInstanceLogListFromResult = (result: any) => {
      setProcessInstanceLogs(result.results);
      setPagination(result.pagination);
    };
    const { page, perPage } = getPageInfoFromSearchParams(searchParams);
    HttpService.makeCallToBackend({
      path: `/process-instances/${params.process_instance_id}/logs?per_page=${perPage}&page=${page}`,
      successCallback: setProcessInstanceLogListFromResult,
    });
  }, [searchParams, params]);

  const buildTable = () => {
    const rows = processInstanceLogs.map((row) => {
      const rowToUse = row as any;
      return (
        <tr key={rowToUse.id}>
          <td>{rowToUse.bpmn_process_identifier}</td>
          <td>{rowToUse.message}</td>
          <td>{rowToUse.bpmn_task_identifier}</td>
          <td>{rowToUse.bpmn_task_name}</td>
          <td>{rowToUse.bpmn_task_type}</td>
          <td>{rowToUse.username}</td>
          <td>
            <Link
              data-qa="process-instance-show-link"
              to={`/admin/process-models/${modifiedProcessModelId}/process-instances/${rowToUse.process_instance_id}/${rowToUse.spiff_step}`}
            >
              {convertSecondsToFormattedDateTime(rowToUse.timestamp)}
            </Link>
          </td>
        </tr>
      );
    });
    return (
      <Table size="lg">
        <thead>
          <tr>
            <th>Bpmn Process Identifier</th>
            <th>Message</th>
            <th>Task Identifier</th>
            <th>Task Name</th>
            <th>Task Type</th>
            <th>User</th>
            <th>Timestamp</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </Table>
    );
  };

  if (pagination) {
    const { page, perPage } = getPageInfoFromSearchParams(searchParams);
    return (
      <main>
        <ProcessBreadcrumb
          hotCrumbs={[
            ['Process Groups', '/admin'],
            [
              `Process Model: ${params.process_model_id}`,
              `process_model:${unModifyProcessIdentifierForPathParam(
                params.process_model_id || ''
              )}:link`,
            ],
            [
              `Process Instance: ${params.process_instance_id}`,
              `/admin/process-models/${params.process_model_id}/process-instances/${params.process_instance_id}`,
            ],
            ['Logs'],
          ]}
        />
        <PaginationForTable
          page={page}
          perPage={perPage}
          pagination={pagination}
          tableToDisplay={buildTable()}
        />
      </main>
    );
  }
  return null;
}
