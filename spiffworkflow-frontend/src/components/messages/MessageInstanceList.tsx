import { useEffect, useState } from 'react';
import { ErrorOutline } from '@mui/icons-material';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  Typography,
} from '@mui/material';
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
import SpiffTooltip from '../SpiffTooltip';

type OwnProps = {
  processInstanceId?: number;
};

const paginationQueryParamPrefix = 'message-list';

export default function MessageInstanceList({ processInstanceId }: OwnProps) {
  const [messageInstances, setMessageInstances] = useState([]);
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
            <Typography variant="body1" className="failure-string">
              {messageInstanceForModal.failure_cause}
            </Typography>
            <br />
          </>
        );
      }
      return (
        <Dialog
          open={!!messageInstanceForModal}
          onClose={handleCorrelationDisplayClose}
          aria-labelledby="dialog-title"
          aria-describedby="dialog-description"
        >
          <DialogTitle id="dialog-title">
            Message {messageInstanceForModal.id} ({messageInstanceForModal.name}
            ) {messageInstanceForModal.message_type} data:
          </DialogTitle>
          <DialogContent>
            {failureCausePre}
            <DialogContentText>Correlations:</DialogContentText>
            <pre>
              {JSON.stringify(
                messageInstanceForModal.correlation_keys,
                null,
                2,
              )}
            </pre>
          </DialogContent>
        </Dialog>
      );
    }
    return null;
  };

  const buildTable = () => {
    const rows = messageInstances.map((row: MessageInstance) => {
      let errorIcon = null;
      let errorTitle = null;
      if (row.failure_cause) {
        errorTitle = 'Instance has an error';
        errorIcon = (
          <>
            &nbsp;
            <ErrorOutline style={{ fill: 'red' }} />
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
        <TableRow key={row.id}>
          <TableCell>{row.id}</TableCell>
          <TableCell>{processLink}</TableCell>
          <TableCell>{instanceLink}</TableCell>
          <TableCell>{row.name}</TableCell>
          <TableCell>{row.message_type}</TableCell>
          <TableCell>{row.counterpart_id}</TableCell>
          <TableCell>
            <SpiffTooltip title={errorTitle}>
              <Button
                variant="text"
                onClick={() => setMessageInstanceForModal(row)}
              >
                View
                {errorIcon}
              </Button>
            </SpiffTooltip>
          </TableCell>
          <TableCell>{row.status}</TableCell>
          <TableCell>
            {DateAndTimeService.convertSecondsToFormattedDateTime(
              row.created_at_in_seconds,
            )}
          </TableCell>
        </TableRow>
      );
    });
    return (
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Id</TableCell>
              <TableCell>Process</TableCell>
              <TableCell>Process instance</TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Corresponding Message Instance</TableCell>
              <TableCell>Details</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Created at</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>{rows}</TableBody>
        </Table>
      </TableContainer>
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
