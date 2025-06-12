import { useState } from 'react';
import { useTranslation } from 'react-i18next';
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
  buttonText,
  reportMetadata,
}: OwnProps) {
  const { t } = useTranslation();
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
      label={t('identifier')}
      variant="outlined"
      fullWidth
      value={identifier}
      onChange={(e: any) => setIdentifier(e.target.value)}
    />
  );

  let descriptionText = t('save_perspective_description');
  if (processInstanceReportSelection) {
    descriptionText = t('save_perspective_edit_description');
  }

  return (
    <Stack direction="row" spacing={2}>
      <Dialog
        open={showSaveForm}
        onClose={handleSaveFormClose}
        aria-labelledby="save-perspective-dialog"
      >
        <DialogTitle id="save-perspective-dialog">{t('save_perspective')}</DialogTitle>
        <DialogContent>
          <Typography variant="body2" style={{ marginBottom: '1rem' }}>
            {descriptionText}
          </Typography>
          {textInputComponent}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleSaveFormClose} color="primary">
            {t('cancel')}
          </Button>
          <Button
            onClick={addProcessInstanceReport}
            color="primary"
            disabled={!identifier}
          >
            {t('save')}
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
        {buttonText ? buttonText : t('save_as_perspective')}
      </Button>
    </Stack>
  );
}
