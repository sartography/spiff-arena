import React, { useCallback, useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  Alert,
  AlertTitle,
  CircularProgress,
  Typography,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

import { green } from '@mui/material/colors';
import { DataGrid } from '@mui/x-data-grid';
import HttpService from '../services/HttpService';

import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import { MigrationEvent, MigrationCheckResult } from '../interfaces';
import CellRenderer from '../a-spiffui-v2/views/Dashboards/myProcesses/CellRenderer';

function DangerousMigrationButton({
  successCallback,
  failureCallback,
  targetBpmnProcessHash,
  title,
  buttonText = 'Migrate to Newest',
}: {
  successCallback: (result: any) => void;
  failureCallback: (error: any) => void;
  title?: string;
  targetBpmnProcessHash?: string;
  buttonText?: string;
}) {
  const params = useParams();
  const [openDialog, setOpenDialog] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const { targetUris } = useUriListForPermissions();
  const [migrationCheckResult, setMigrationCheckResult] =
    useState<MigrationCheckResult | null>(null);

  useEffect(() => {
    let queryParams = '';
    if (targetBpmnProcessHash) {
      queryParams = `?target_bpmn_process_hash=${targetBpmnProcessHash}`;
    }
    HttpService.makeCallToBackend({
      path: `/process-instances/${params.process_model_id}/${params.process_instance_id}/check-can-migrate${queryParams}`,
      successCallback: (result: any) => setMigrationCheckResult(result),
    });
  }, [
    targetBpmnProcessHash,
    params.process_model_id,
    params.process_instance_id,
  ]);

  const handleRunMigration = () => {
    setIsLoading(true);
    let queryParams = '';
    if (targetBpmnProcessHash) {
      queryParams = `?target_bpmn_process_hash=${targetBpmnProcessHash}`;
    }
    HttpService.makeCallToBackend({
      httpMethod: 'POST',
      path: `${targetUris.processInstanceMigratePath}${queryParams}`,
      successCallback: (result: any) => {
        setIsLoading(false);
        setOpenDialog(false);
        successCallback(result);
      },
      failureCallback: (error: any) => {
        setIsLoading(false);
        setOpenDialog(false);
        failureCallback(error);
      },
    });
  };

  const handleOpenDialog = () => {
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
  };

  if (migrationCheckResult?.can_migrate) {
    return (
      <>
        <Button
          variant="contained"
          color="secondary"
          onClick={handleOpenDialog}
          title={title}
          size="small"
        >
          {buttonText}
        </Button>

        <Dialog open={openDialog} onClose={handleCloseDialog}>
          <DialogTitle>Confirm Migrate Instance</DialogTitle>
          <DialogContent>
            <DialogContentText>
              Are you sure you want to proceed with this potentially-dangerous
              process instance migration?
            </DialogContentText>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseDialog} disabled={isLoading}>
              Cancel
            </Button>
            <Button
              onClick={handleRunMigration}
              color="secondary"
              variant="contained"
              disabled={isLoading}
            >
              {isLoading ? <CircularProgress size={24} /> : 'Confirm'}
            </Button>
          </DialogActions>
        </Dialog>
      </>
    );
  }
  return null;
}
function MigrationStatus({
  migrationCheckResult,
}: {
  migrationCheckResult: any | null;
}) {
  let returnComponent = null;
  if (migrationCheckResult === null) {
    returnComponent = (
      <>
        <CircularProgress style={{ marginRight: 8 }} />
        <Typography>Checking if ready to migrate</Typography>
      </>
    );
  } else if (migrationCheckResult.can_migrate) {
    returnComponent = (
      <>
        <CheckCircleIcon style={{ color: green[500], marginRight: 8 }} />
        <Typography>
          Ready to migrate to newest process model version
        </Typography>
      </>
    );
  } else if (
    migrationCheckResult.exception_class ===
    'ProcessInstanceMigrationUnnecessaryError'
  ) {
    returnComponent = (
      <Alert severity="success">
        <AlertTitle>Nothing to migrate</AlertTitle>The process instance is
        already associated with the most recent process model version.
      </Alert>
    );
  } else {
    returnComponent = (
      <Alert severity="warning">
        <AlertTitle>Process instance not migratable</AlertTitle>
        Process Instances can be migrated if the target process model version
        has not changed any of the tasks that have already been completed and if
        the process instance is not already at the newest version.
      </Alert>
    );
  }
  return (
    <Box display="flex" alignItems="center">
      {returnComponent}
    </Box>
  );
}

export default function ProcessInstanceMigratePage() {
  const params = useParams();
  const [migrationCheckResult, setMigrationCheckResult] =
    useState<MigrationCheckResult | null>(null);
  const [migrationResult, setMigrationResult] = useState<any>(null);
  const [migrationEvents, setMigrationEvents] = useState<
    MigrationEvent[] | null
  >(null);

  const fetchProcessInstanceMigrationDetails = useCallback(() => {
    HttpService.makeCallToBackend({
      path: `/process-instances/${params.process_model_id}/${params.process_instance_id}/check-can-migrate`,
      successCallback: (result: any) => setMigrationCheckResult(result),
    });
    HttpService.makeCallToBackend({
      path: `/process-instance-events/${params.process_model_id}/${params.process_instance_id}/migration`,
      successCallback: (result: any) => setMigrationEvents(result.results),
    });
  }, [params.process_instance_id, params.process_model_id]);

  useEffect(fetchProcessInstanceMigrationDetails, [
    fetchProcessInstanceMigrationDetails,
  ]);

  const onMigrationComplete = (result: any) => {
    fetchProcessInstanceMigrationDetails();
    setMigrationResult(result);
  };
  const onMigrationFailure = (error: any) => {
    setMigrationResult(error);
  };

  const migrationResultComponent = () => {
    if (!migrationResult) {
      return null;
    }

    if (migrationResult.ok) {
      return <Alert severity="success">Process instance migrated</Alert>;
    }

    let alertBody = null;
    if (typeof migrationResult === 'string') {
      alertBody = migrationResult;
    } else if (
      typeof migrationResult === 'object' &&
      migrationResult.error_code
    ) {
      alertBody = migrationResult.message;
    } else {
      alertBody = (
        <ul>
          {Object.keys(migrationResult).map((key) => (
            <li key={key}>
              {key}: {migrationResult[key]}
            </li>
          ))}
        </ul>
      );
    }
    return (
      <Alert severity="error">
        <AlertTitle>Error</AlertTitle>
        {alertBody}
      </Alert>
    );
  };

  const processInstanceMigrationEventTable = () => {
    if (!migrationEvents || migrationEvents.length === 0) {
      return null;
    }

    const columns = [
      {
        field: 'username',
        headerName: 'Username',
        flex: 2,
        renderCell: (data: Record<string, any>) => {
          return <CellRenderer header="username" data={data} />;
        },
      },
      {
        field: 'timestamp',
        headerName: 'Timestamp',
        flex: 2,
        renderCell: (data: Record<string, any>) => {
          return <CellRenderer header="timestamp" data={data} />;
        },
      },
      {
        field: 'initial_git_revision',
        headerName: 'Initial Git Revision',
        flex: 2,
        renderCell: (data: Record<string, any>) => {
          return (
            <CellRenderer
              header="initial_git_revision"
              data={data}
              title={data.row.initial_bpmn_process_hash}
            />
          );
        },
      },
      {
        field: 'target_git_revision',
        headerName: 'Target Git Revision',
        flex: 2,
        renderCell: (data: Record<string, any>) => {
          return (
            <CellRenderer
              header="target_git_revision"
              data={data}
              title={data.row.target_bpmn_process_hash}
            />
          );
        },
      },
      {
        field: 'actions',
        headerName: 'Actions',
        flex: 2,
        renderCell: (data: Record<string, any>) => {
          if (
            migrationCheckResult &&
            data.row.initial_bpmn_process_hash ===
              migrationCheckResult.current_bpmn_process_hash
          ) {
            return null;
          }
          return (
            <DangerousMigrationButton
              successCallback={onMigrationComplete}
              failureCallback={onMigrationFailure}
              title={`Run another migration to switch to model version: '${data.row.initial_git_revision}'`}
              targetBpmnProcessHash={data.row.initial_bpmn_process_hash}
              buttonText="Revert"
            />
          );
        },
      },
    ];
    const rows = migrationEvents.map((migrationEvent: MigrationEvent) => {
      return migrationEvent;
    });
    return (
      <>
        <h3>Previous Migrations</h3>
        <DataGrid
          sx={{
            '& .MuiDataGrid-cell:focus': {
              outline: 'none',
            },
          }}
          initialState={{
            columns: {
              columnVisibilityModel: {
                status: false,
                last_milestone_bpmn_name: false,
              },
            },
          }}
          autoHeight
          getRowHeight={() => 'auto'}
          rows={rows}
          columns={columns}
          hideFooter
        />
      </>
    );
  };

  return (
    <>
      <ProcessBreadcrumb
        hotCrumbs={[
          ['Process Groups', '/process-groups'],
          {
            entityToExplode: String(params.process_model_id),
            entityType: 'process-model-id',
            linkLastItem: true,
          },
          [
            `Process Instance: ${params.process_instance_id}`,
            `/i/${params.process_instance_id}`,
          ],
          ['Migrate'],
        ]}
      />
      <br />
      {migrationResultComponent()}
      <br />
      <MigrationStatus migrationCheckResult={migrationCheckResult} />
      <br />
      {migrationCheckResult?.can_migrate ? (
        <DangerousMigrationButton
          successCallback={onMigrationComplete}
          failureCallback={onMigrationFailure}
        />
      ) : null}
      <br />
      <br />
      {processInstanceMigrationEventTable()}
    </>
  );
}
