import React from 'react';
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import { CircularProgress, Typography, Box } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import HighlightOffIcon from '@mui/icons-material/HighlightOff';

import { green, red } from '@mui/material/colors';
import HttpService from '../services/HttpService';

import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
} from '@mui/material';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';

export default function ProcessInstanceMigratePage() {
  const params = useParams();
  const [canBeMigrated, setCanBeMigrated] = useState<boolean | null>(null);
  const { targetUris } = useUriListForPermissions();

  useEffect(() => {
    HttpService.makeCallToBackend({
      path: `/process-instances/${params.process_model_id}/${params.process_instance_id}/check-can-migrate`,
      successCallback: (result: any) => setCanBeMigrated(result.can_migrate),
    });
  }, []);

  const DangerousMigrationButton = () => {
    const [openDialog, setOpenDialog] = useState(false);
    const [isLoading, setIsLoading] = useState(false);

    const handleRunMigration = () => {
      // Simulate loading process
      setIsLoading(true);
      // setTimeout(() => {
      //   setIsLoading(false);
      //   setOpenDialog(false); // Close dialog after successful migration
      //   // Perform actual migration logic here
      //   console.log('Migration process completed successfully.');
      // }, 2000); // Simulate a delay

      // Uncomment the line below to prevent dialog auto-closing during loading
      // setOpenDialog(false);
      HttpService.makeCallToBackend({
        httpMethod: 'POST',
        path: targetUris.processInstanceMigratePath,
        successCallback: (result: any) => {
          setIsLoading(false);
          setOpenDialog(false);
        },
        failureCallback: (result: any) => {
          setIsLoading(false);
          setOpenDialog(false);
          console.error(result);
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
        <Button
          variant="contained"
          color="secondary"
          onClick={handleOpenDialog}
        >
          Run Dangerous Migration
        </Button>

        <Dialog open={openDialog} onClose={handleCloseDialog}>
          <DialogTitle>Confirm Dangerous Migration</DialogTitle>
          <DialogContent>
            <DialogContentText>
              Are you sure you want to proceed with this dangerous migration?
              This action cannot be undone.
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
  };

  const MigrationStatus = ({ isReady }: { isReady: boolean | null }) => {
    return (
      <Box display="flex" alignItems="center">
        {isReady ? (
          <>
            <CheckCircleIcon style={{ color: green[500], marginRight: 8 }} />
            <Typography>Ready to migrate</Typography>
          </>
        ) : isReady === null ? (
          <>
            <CircularProgress style={{ marginRight: 8 }} />
            <Typography>Checking if ready to migrate</Typography>
          </>
        ) : (
          <>
            <HighlightOffIcon style={{ color: red[500], marginRight: 8 }} />
            <Typography>Not ready to migrate</Typography>
          </>
        )}
      </Box>
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
      <MigrationStatus isReady={canBeMigrated} />
      {canBeMigrated ? <DangerousMigrationButton /> : null}
    </>
  );
}
