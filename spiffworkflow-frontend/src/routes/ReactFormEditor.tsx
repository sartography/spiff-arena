import { useContext, useEffect, useState } from 'react';
import Editor from '@monaco-editor/react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
// @ts-ignore
import { Button, Modal } from '@carbon/react';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import HttpService from '../services/HttpService';
import ButtonWithConfirmation from '../components/ButtonWithConfirmation';
import { modifyProcessIdentifierForPathParam } from '../helpers';
import { ProcessFile } from '../interfaces';
import ErrorContext from '../contexts/ErrorContext';
import { Notification } from '../components/Notification';

// NOTE: This is mostly the same as ProcessModelEditDiagram and if we go this route could
// possibly be merged into it. I'm leaving as a separate file now in case it does
// end up diverging greatly
export default function ReactFormEditor() {
  const params = useParams();
  const setErrorObject = (useContext as any)(ErrorContext)[1];

  const [showFileNameEditor, setShowFileNameEditor] = useState(false);
  const [newFileName, setNewFileName] = useState('');
  const searchParams = useSearchParams()[0];
  const handleShowFileNameEditor = () => setShowFileNameEditor(true);
  const navigate = useNavigate();

  const [displaySaveFileMessage, setDisplaySaveFileMessage] =
    useState<boolean>(false);

  const [processModelFile, setProcessModelFile] = useState<ProcessFile | null>(
    null
  );
  const [processModelFileContents, setProcessModelFileContents] = useState('');

  const fileExtension = (() => {
    if (params.file_name) {
      const matches = params.file_name.match(/\.([a-z]+)/);
      if (matches !== null && matches.length > 1) {
        return matches[1];
      }
    }

    return searchParams.get('file_ext') ?? 'json';
  })();

  const hasDiagram = fileExtension === 'bpmn' || fileExtension === 'dmn';

  const editorDefaultLanguage = (() => {
    if (fileExtension === 'json') {
      return 'json';
    }
    if (hasDiagram) {
      return 'xml';
    }
    if (fileExtension === 'md') {
      return 'markdown';
    }
    return 'text';
  })();

  const modifiedProcessModelId = modifyProcessIdentifierForPathParam(
    `${params.process_model_id}`
  );

  useEffect(() => {
    const processResult = (result: any) => {
      setProcessModelFile(result);
      setProcessModelFileContents(result.file_contents);
    };

    if (params.file_name) {
      HttpService.makeCallToBackend({
        path: `/process-models/${modifiedProcessModelId}/files/${params.file_name}`,
        successCallback: processResult,
      });
    }
  }, [params, modifiedProcessModelId]);

  const navigateToProcessModelFile = (_result: any) => {
    setDisplaySaveFileMessage(true);
    if (!params.file_name) {
      const fileNameWithExtension = `${newFileName}.${fileExtension}`;
      navigate(
        `/admin/process-models/${modifiedProcessModelId}/form/${fileNameWithExtension}`
      );
    }
  };

  const saveFile = () => {
    setErrorObject(null);
    setDisplaySaveFileMessage(false);

    let url = `/process-models/${modifiedProcessModelId}/files`;
    let httpMethod = 'PUT';
    let fileNameWithExtension = params.file_name;

    if (newFileName) {
      fileNameWithExtension = `${newFileName}.${fileExtension}`;
      httpMethod = 'POST';
    } else {
      url += `/${fileNameWithExtension}`;
    }
    if (!fileNameWithExtension) {
      handleShowFileNameEditor();
      return;
    }

    const file = new File(
      [processModelFileContents],
      fileNameWithExtension || ''
    );
    const formData = new FormData();
    formData.append('file', file);
    formData.append('fileName', file.name);

    HttpService.makeCallToBackend({
      path: url,
      successCallback: navigateToProcessModelFile,
      failureCallback: setErrorObject,
      httpMethod,
      postBody: formData,
    });
  };

  const deleteFile = () => {
    const url = `/process-models/${modifiedProcessModelId}/files/${params.file_name}`;
    const httpMethod = 'DELETE';

    const navigateToProcessModelShow = (_httpResult: any) => {
      navigate(`/admin/process-models/${modifiedProcessModelId}`);
    };

    HttpService.makeCallToBackend({
      path: url,
      successCallback: navigateToProcessModelShow,
      httpMethod,
    });
  };

  const handleFileNameCancel = () => {
    setShowFileNameEditor(false);
    setNewFileName('');
  };

  const handleFileNameSave = (event: any) => {
    event.preventDefault();
    setShowFileNameEditor(false);
    saveFile();
  };

  const newFileNameBox = () => {
    return (
      <Modal
        open={showFileNameEditor}
        modalHeading="Processs Model File Name"
        primaryButtonText="Save Changes"
        secondaryButtonText="Cancel"
        onSecondarySubmit={handleFileNameCancel}
        onRequestSubmit={handleFileNameSave}
        onRequestClose={handleFileNameCancel}
      >
        <label>File Name:</label>
        <span>
          <input
            name="file_name"
            type="text"
            value={newFileName}
            onChange={(e) => setNewFileName(e.target.value)}
            autoFocus
          />
          {fileExtension}
        </span>
      </Modal>
    );
  };

  const saveFileMessage = () => {
    if (displaySaveFileMessage) {
      return (
        <Notification
          title="File Saved: "
          onClose={() => setDisplaySaveFileMessage(false)}
        >
          Changes to the file were saved.
        </Notification>
      );
    }
    return null;
  };

  if (processModelFile || !params.file_name) {
    const processModelFileName = processModelFile ? processModelFile.name : '';
    const formBuildFileParam = params.file_name
      ? `?file_name=${params.file_name}`
      : '';
    return (
      <main>
        <ProcessBreadcrumb
          hotCrumbs={[
            ['Process Groups', '/admin'],
            {
              entityToExplode: params.process_model_id || '',
              entityType: 'process-model-id',
              linkLastItem: true,
            },
            [processModelFileName],
          ]}
        />
        <h1>
          Process Model File{processModelFile ? ': ' : ''}
          {processModelFileName}
        </h1>
        {newFileNameBox()}
        {saveFileMessage()}
        <Button onClick={saveFile} variant="danger" data-qa="file-save-button">
          Save
        </Button>

        {params.file_name ? (
          <ButtonWithConfirmation
            data-qa="delete-process-model-file"
            description={`Delete file ${params.file_name}?`}
            onConfirmation={deleteFile}
            buttonLabel="Delete"
          />
        ) : null}
        <Button
          onClick={() =>
            navigate(
              `/admin/process-models/${params.process_model_id}/form-builder${formBuildFileParam}`
            )
          }
          variant="danger"
          data-qa="form-builder-button"
        >
          Form Builder
        </Button>
        {hasDiagram ? (
          <Button
            onClick={() =>
              navigate(
                `/admin/process-models/${modifiedProcessModelId}/files/${params.file_name}`
              )
            }
            variant="danger"
            data-qa="view-diagram-button"
          >
            View Diagram
          </Button>
        ) : null}
        <Editor
          height={600}
          width="auto"
          defaultLanguage={editorDefaultLanguage}
          defaultValue={processModelFileContents || ''}
          onChange={(value) => setProcessModelFileContents(value || '')}
        />
      </main>
    );
  }
  return <main />;
}
