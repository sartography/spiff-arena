import React, { useEffect, useState } from 'react';
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
import HttpService from '../services/HttpService';

import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';

function DangerousMigrationButton({
  successCallback,
  failureCallback,
}: {
  successCallback: Function;
  failureCallback: Function;
}) {
  const [openDialog, setOpenDialog] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const { targetUris } = useUriListForPermissions();

  const handleRunMigration = () => {
    setIsLoading(true);
    HttpService.makeCallToBackend({
      httpMethod: 'POST',
      path: targetUris.processInstanceMigratePath,
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

  return (
    <>
      <Button variant="contained" color="secondary" onClick={handleOpenDialog}>
        Run Dangerous Migration
      </Button>

      <Dialog open={openDialog} onClose={handleCloseDialog}>
        <DialogTitle>Confirm Dangerous Migration</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to proceed with this dangerous migration? This
            action cannot be undone.
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
function MigrationStatus({ isReady }: { isReady: boolean | null }) {
  let returnComponent = null;
  if (isReady) {
    returnComponent = (
      <>
        <CheckCircleIcon style={{ color: green[500], marginRight: 8 }} />
        <Typography>Ready to migrate</Typography>
      </>
    );
  } else if (isReady == null) {
    returnComponent = (
      <>
        <CircularProgress style={{ marginRight: 8 }} />
        <Typography>Checking if ready to migrate</Typography>
      </>
    );
  } else {
    returnComponent = (
      <Alert severity="warning">
        <AlertTitle>Process instance not migratable</AlertTitle>
        Process Instances can be migrated if the target process model version
        has not changed any of the tasks that have already been completed.
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
  const [canBeMigrated, setCanBeMigrated] = useState<boolean | null>(null);
  const [migrationResult, setMigrationResult] = useState<any>(null);

  useEffect(() => {
    HttpService.makeCallToBackend({
      path: `/process-instances/${params.process_model_id}/${params.process_instance_id}/check-can-migrate`,
      successCallback: (result: any) => setCanBeMigrated(result.can_migrate),
    });
  }, [params.process_instance_id, params.process_model_id]);

  const onMigrationComplete = (result: any) => {
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
      <Alert severity="warning">
        <AlertTitle>Unexpected response</AlertTitle>
        {alertBody}
      </Alert>
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
        ]}
      />
      <br />
      {migrationResult !== null ? (
        migrationResultComponent()
      ) : (
        <>
          <MigrationStatus isReady={canBeMigrated} />
          <br />
          {canBeMigrated ? (
            <DangerousMigrationButton
              successCallback={onMigrationComplete}
              failureCallback={onMigrationFailure}
            />
          ) : null}
        </>
      )}
    </>
  );
}
