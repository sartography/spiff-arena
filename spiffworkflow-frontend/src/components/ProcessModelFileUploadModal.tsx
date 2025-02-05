import { useState } from 'react';
import { FileUploader, Modal } from '@carbon/react';

interface ProcessModelFileUploadModalProps {
  showFileUploadModal: boolean;
  processModel: any;
  onFileUpload: (event: any) => void;
  handleFileUploadCancel: () => void;
  checkDuplicateFile: (event: any) => void;
}
interface FileUploadState {
  filesToUpload: File[] | null;
}

const ProcessModelFileUploadModal: React.FC<
  ProcessModelFileUploadModalProps
> = ({
  showFileUploadModal,
  processModel,
  onFileUpload,
  handleFileUploadCancel,
  checkDuplicateFile,
}) => {
  const [filesToUpload, setFilesToUpload] = useState<File[] | null>(null);
  const [duplicateFilename, setDuplicateFilename] = useState<string>('');
  const [showOverwriteConfirmationPrompt, setShowOverwriteConfirmationPrompt] =
    useState(false);
  const [fileUploadEvent, setFileUploadEvent] = useState(null);

  const handleOverwriteFileConfirm = () => {
    setShowOverwriteConfirmationPrompt(false);
    if (fileUploadEvent) {
      checkDuplicateFile(fileUploadEvent, true); // Force overwrite
    }
  };

  const handleOverwriteFileCancel = () => {
    setShowOverwriteConfirmationPrompt(false);
    setFilesToUpload(null);
  };

  const displayOverwriteConfirmation = (filename: string) => {
    setDuplicateFilename(filename);
    setShowOverwriteConfirmationPrompt(true);
  };

  const handleLocalFileUpload = (event: any) => {
    const newFiles: File[] = Array.from(event.target.files);
    setFilesToUpload(newFiles);

    if (processModel) {
      let foundExistingFile = false;
      if (processModel.files.length > 0) {
        processModel.files.forEach((file: { name: string }) => {
          if (file.name === newFiles[0].name) {
            foundExistingFile = true;
          }
        });
      }
      if (foundExistingFile) {
        displayOverwriteConfirmation(newFiles[0].name);
        setFileUploadEvent(event);
      } else {
        checkDuplicateFile(event);
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
        onRequestSubmit={() => {
          if (filesToUpload) {
            checkDuplicateFile(filesToUpload);
          }
          setShowOverwriteConfirmationPrompt(false);
        }}
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
          onChange={handleLocalFileUpload}
        />
      </Modal>
    </>
  );
};

export default ProcessModelFileUploadModal;
