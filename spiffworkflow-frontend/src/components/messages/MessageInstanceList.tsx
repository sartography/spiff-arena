import { useEffect, useState } from 'react';
// @ts-ignore
import { ErrorOutline } from '@carbon/icons-react';
// @ts-ignore
import { Table, Modal, Button } from '@carbon/react';
import { Link, useSearchParams } from 'react-router-dom';
import PaginationForTable from '../PaginationForTable';
import ProcessBreadcrumb from '../ProcessBreadcrumb';
import {
  getPageInfoFromSearchParams,
  modifyProcessIdentifierForPathParam,
} from '../../helpers';
import HttpService from '../../services/HttpService';
import { FormatProcessModelDisplayName } from '../MiniComponents';
import { MessageInstance } from '../../interfaces';
import DateAndTimeService from '../../services/DateAndTimeService';

type OwnProps = {
  processInstanceId?: number;
};

const paginationQueryParamPrefix = 'message-list';

export default function MessageInstanceList({ processInstanceId }: OwnProps) {
  const [messageIntances, setMessageInstances] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [searchParams] = useSearchParams();

  const [messageInstanceForModal, setMessageInstanceForModal] =
    useState<MessageInstance | null>(null);

  useEffect(() => {
    const setMessageInstanceListFromResult = (result: any) => {
      setMessageInstances(result.results);
      setPagination(result.pagination);
    };
    const { page, perPage } = getPageInfoFromSearchParams(
      searchParams,
      undefined,
      undefined,
      paginationQueryParamPrefix,
    );
    let queryParamString = `per_page=${perPage}&page=${page}`;
    if (processInstanceId) {
      queryParamString += `&process_instance_id=${processInstanceId}`;
    }

    HttpService.makeCallToBackend({
      path: `/messages?${queryParamString}`,
      successCallback: setMessageInstanceListFromResult,
    });
  }, [processInstanceId, searchParams]);

  const handleCorrelationDisplayClose = () => {
    setMessageInstanceForModal(null);
  };

  const correlationsDisplayModal = () => {
    if (messageInstanceForModal) {
      let failureCausePre = null;
      if (messageInstanceForModal.failure_cause) {
        failureCausePre = (
          <>
            <p className="failure-string">
              {messageInstanceForModal.failure_cause}
            </p>
            <br />
          </>
        );
      }
      return (
        <Modal
          open={!!messageInstanceForModal}
          passiveModal
          onRequestClose={handleCorrelationDisplayClose}
          modalHeading={`Message ${messageInstanceForModal.id} (${messageInstanceForModal.name}) ${messageInstanceForModal.message_type} data:`}
          modalLabel="Details"
        >
          {failureCausePre}
          <p>Correlations:</p>
          <pre>
            {JSON.stringify(messageInstanceForModal.correlation_keys, null, 2)}
          </pre>
        </Modal>
      );
    }
    return null;
  };

  const buildTable = () => {
    const rows = messageIntances.map((row: MessageInstance) => {
      let errorIcon = null;
      let errorTitle = null;
      if (row.failure_cause) {
        errorTitle = 'Instance has an error';
        errorIcon = (
          <>
            &nbsp;
            <ErrorOutline className="red-icon" />
          </>
        );
      }
      let processLink = <span>External Call</span>;
      let instanceLink = <span />;
      if (row.process_instance_id != null) {
        processLink = FormatProcessModelDisplayName(row);
        instanceLink = (
          <Link
            data-qa="process-instance-show-link"
            to={`/process-instances/${modifyProcessIdentifierForPathParam(
              row.process_model_identifier,
            )}/${row.process_instance_id}`}
          >
            {row.process_instance_id}
          </Link>
        );
      }
      return (
        <tr key={row.id}>
          <td>{row.id}</td>
          <td>{processLink}</td>
          <td>{instanceLink}</td>
          <td>{row.name}</td>
          <td>{row.message_type}</td>
          <td>{row.counterpart_id}</td>
          <td>
            <Button
              kind="ghost"
              className="button-link"
              onClick={() => setMessageInstanceForModal(row)}
              title={errorTitle}
            >
              View
              {errorIcon}
            </Button>
          </td>
          <td>{row.status}</td>
          <td>
            {DateAndTimeService.convertSecondsToFormattedDateTime(
              row.created_at_in_seconds,
            )}
          </td>
        </tr>
      );
    });
    return (
      <Table striped bordered>
        <thead>
          <tr>
            <th>Id</th>
            <th>Process</th>
            <th>Process instance</th>
            <th>Name</th>
            <th>Type</th>
            <th>Corresponding Message Instance</th>
            <th>Details</th>
            <th>Status</th>
            <th>Created at</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </Table>
    );
  };

  if (pagination) {
    const { page, perPage } = getPageInfoFromSearchParams(
      searchParams,
      undefined,
      undefined,
      paginationQueryParamPrefix,
    );
    let breadcrumbElement = null;
    if (searchParams.get('process_instance_id')) {
      breadcrumbElement = (
        <ProcessBreadcrumb
          hotCrumbs={[
            ['Process Groups', '/process-groups'],
            {
              entityToExplode: searchParams.get('process_model_id') || '',
              entityType: 'process-model-id',
              linkLastItem: true,
            },
            [
              `Process Instance: ${searchParams.get('process_instance_id')}`,
              `/process-instances/${searchParams.get(
                'process_model_id',
              )}/${searchParams.get('process_instance_id')}`,
            ],
            ['Messages'],
          ]}
        />
      );
    }
    return (
      <>
        {breadcrumbElement}
        {correlationsDisplayModal()}
        <PaginationForTable
          page={page}
          perPage={perPage}
          perPageOptions={[10, 50, 100, 500, 1000]}
          pagination={pagination}
          tableToDisplay={buildTable()}
          paginationQueryParamPrefix={paginationQueryParamPrefix}
        />
      </>
    );
  }
  return null;
}
