import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
} from '@mui/material';
import SpiffTooltip from './SpiffTooltip';

interface ProcessModelFileUploadModalProps {
  showFileUploadModal: boolean;
  processModel: any;
  handleFileUploadCancel: () => void;
  checkDuplicateFile: (files: File[], forceOverwrite?: boolean) => void;
  doFileUpload: Function;
  setShowFileUploadModal: Function;
}

export default function ProcessModelFileUploadModal({
  showFileUploadModal,
  processModel,
  handleFileUploadCancel,
  checkDuplicateFile,
  doFileUpload,
  setShowFileUploadModal,
}: ProcessModelFileUploadModalProps) {
  const [filesToUpload, setFilesToUpload] = useState<File[] | null>(null);
  const [duplicateFilename, setDuplicateFilename] = useState<string>('');
  const [showOverwriteConfirmationPrompt, setShowOverwriteConfirmationPrompt] =
    useState(false);
  const { t } = useTranslation();

  const handleOverwriteFileConfirm = () => {
    setShowOverwriteConfirmationPrompt(false);
    doFileUpload(filesToUpload);
  };

  const handleOverwriteFileCancel = () => {
    setShowFileUploadModal(true);
    setShowOverwriteConfirmationPrompt(false);
  };

  const displayOverwriteConfirmation = (filename: string) => {
    setDuplicateFilename(filename);
    setShowFileUploadModal(false);
    setShowOverwriteConfirmationPrompt(true);
  };

  const handleLocalFileUpload = () => {
    if (!filesToUpload) {
      return;
    }
    if (processModel) {
      let foundExistingFile = false;
      if (processModel.files && processModel.files.length > 0) {
        processModel.files.forEach((file: { name: string }) => {
          if (file.name === filesToUpload[0].name) {
            foundExistingFile = true;
          }
        });
      }
      if (foundExistingFile) {
        displayOverwriteConfirmation(filesToUpload[0].name);
      } else {
        checkDuplicateFile(filesToUpload);
        setShowOverwriteConfirmationPrompt(false);
      }
    }
  };

  const confirmOverwriteFileDialog = () => {
    return (
      <Dialog
        open={showOverwriteConfirmationPrompt}
        onClose={handleOverwriteFileCancel}
        aria-labelledby="overwrite-dialog-title"
      >
        <DialogTitle id="overwrite-dialog-title">
          {t('overwrite_file')}
        </DialogTitle>
        <DialogContent>
          <Typography>
            {t('overwrite_file_description', { filename: duplicateFilename })}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleOverwriteFileCancel} color="primary">
            {t('cancel')}
          </Button>
          <Button
            onClick={handleOverwriteFileConfirm}
            color="primary"
            autoFocus
          >
            {t('yes')}
          </Button>
        </DialogActions>
      </Dialog>
    );
  };

  return (
    <>
      {confirmOverwriteFileDialog()}
      <Dialog
        open={showFileUploadModal}
        onClose={handleFileUploadCancel}
        aria-labelledby="upload-dialog-title"
      >
        <DialogTitle id="upload-dialog-title">{t('upload_file')}</DialogTitle>
        <DialogContent>
          <Typography>{t('upload_file_instructions')}</Typography>
          <SpiffTooltip title={t('delete_file')}>
            <input
              type="file"
              accept=".bpmn,.dmn,.json,.md"
              onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                setFilesToUpload(
                  event.target.files ? Array.from(event.target.files) : null,
                )
              }
            />
          </SpiffTooltip>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleFileUploadCancel} color="primary">
            {t('cancel')}
          </Button>
          <Button
            onClick={handleLocalFileUpload}
            color="primary"
            disabled={filesToUpload === null}
          >
            {t('upload_button')}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
