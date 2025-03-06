import { useState } from 'react';
import {
  Button,
  TextField,
  Stack,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
} from '@mui/material';
import { ProcessInstanceReport, ReportMetadata } from '../interfaces';
import HttpService from '../services/HttpService';

type OwnProps = {
  onSuccess: (..._args: any[]) => any;
  buttonText?: string;
  buttonClassName?: string;
  processInstanceReportSelection?: ProcessInstanceReport | null;
  reportMetadata: ReportMetadata | null;
};

export default function ProcessInstanceListSaveAsReport({
  onSuccess,
  processInstanceReportSelection,
  buttonClassName,
  buttonText = 'Save as Perspective',
  reportMetadata,
}: OwnProps) {
  const [identifier, setIdentifier] = useState<string>(
    processInstanceReportSelection?.identifier || '',
  );
  const [showSaveForm, setShowSaveForm] = useState<boolean>(false);

  const isEditMode = () => {
    return (
      processInstanceReportSelection &&
      processInstanceReportSelection.identifier === identifier
    );
  };

  const responseHandler = (result: any) => {
    if (result) {
      onSuccess(result, isEditMode() ? 'edit' : 'new');
    }
  };

  const handleSaveFormClose = () => {
    setIdentifier(processInstanceReportSelection?.identifier || '');
    setShowSaveForm(false);
  };

  const addProcessInstanceReport = (event: any) => {
    event.preventDefault();

    let path = `/process-instances/reports`;
    let httpMethod = 'POST';
    if (isEditMode() && processInstanceReportSelection) {
      httpMethod = 'PUT';
      path = `${path}/${processInstanceReportSelection.id}`;
    }

    HttpService.makeCallToBackend({
      path,
      successCallback: responseHandler,
      httpMethod,
      postBody: {
        identifier,
        report_metadata: reportMetadata,
      },
    });
    handleSaveFormClose();
  };

  let textInputComponent = null;
  textInputComponent = (
    <TextField
      id="identifier"
      name="identifier"
      label="Identifier"
      variant="outlined"
      fullWidth
      value={identifier}
      onChange={(e: any) => setIdentifier(e.target.value)}
    />
  );

  let descriptionText =
    'Save the current columns and filters as a perspective so you can come back to this view in the future.';
  if (processInstanceReportSelection) {
    descriptionText =
      'Keep the identifier the same and click Save to update the current perspective. Change the identifier if you want to save the current view with a new name.';
  }

  return (
    <Stack direction="row" spacing={2}>
      <Dialog
        open={showSaveForm}
        onClose={handleSaveFormClose}
        aria-labelledby="save-perspective-dialog"
      >
        <DialogTitle id="save-perspective-dialog">Save Perspective</DialogTitle>
        <DialogContent>
          <Typography variant="body2" style={{ marginBottom: '1rem' }}>
            {descriptionText}
          </Typography>
          {textInputComponent}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleSaveFormClose} color="primary">
            Cancel
          </Button>
          <Button
            onClick={addProcessInstanceReport}
            color="primary"
            disabled={!identifier}
          >
            Save
          </Button>
        </DialogActions>
      </Dialog>
      <Button
        variant="outlined"
        className={buttonClassName}
        onClick={() => {
          setIdentifier(processInstanceReportSelection?.identifier || '');
          setShowSaveForm(true);
        }}
      >
        {buttonText}
      </Button>
    </Stack>
  );
}
