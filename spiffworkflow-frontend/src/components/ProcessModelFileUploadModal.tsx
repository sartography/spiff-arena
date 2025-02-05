import React, { useState } from 'react';
import { FileUploader, Modal } from '@carbon/react';

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
      <Modal
        danger
        open={showOverwriteConfirmationPrompt}
        data-qa="file-overwrite-modal-confirmation-dialog"
        modalHeading={`Overwrite the file: ${duplicateFilename}`}
        modalLabel="Overwrite file?"
        primaryButtonText="Yes"
        secondaryButtonText="Cancel"
        onSecondarySubmit={handleOverwriteFileCancel}
        onRequestSubmit={handleOverwriteFileConfirm}
        onRequestClose={handleOverwriteFileCancel}
      />
    );
  };

  return (
    <>
      {confirmOverwriteFileDialog()}
      <Modal
        data-qa="modal-upload-file-dialog"
        open={showFileUploadModal}
        modalHeading="Upload File"
        primaryButtonText="Upload"
        primaryButtonDisabled={filesToUpload === null}
        secondaryButtonText="Cancel"
        onSecondarySubmit={handleFileUploadCancel}
        onRequestClose={handleFileUploadCancel}
        onRequestSubmit={handleLocalFileUpload}
      >
        <FileUploader
          labelTitle="Upload files"
          labelDescription="Max file size is 500mb. Only .bpmn, .dmn, .json, and .md files are supported."
          buttonLabel="Add file"
          buttonKind="primary"
          size="md"
          filenameStatus="edit"
          role="button"
          accept={['.bpmn', '.dmn', '.json', '.md']}
          disabled={false}
          iconDescription="Delete file"
          name=""
          multiple={false}
          onDelete={() => setFilesToUpload(null)}
          onChange={(event: any) => setFilesToUpload(event.target.files)}
        />
      </Modal>
    </>
  );
}
