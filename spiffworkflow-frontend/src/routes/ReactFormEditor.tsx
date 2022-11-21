import { useEffect, useState } from 'react';
import Editor from '@monaco-editor/react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
// @ts-ignore
import { Button, Modal } from '@carbon/react';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import HttpService from '../services/HttpService';
import ButtonWithConfirmation from '../components/ButtonWithConfirmation';
import { modifyProcessModelPath, unModifyProcessModelPath } from '../helpers';
import { ProcessFile } from '../interfaces';

// NOTE: This is mostly the same as ProcessModelEditDiagram and if we go this route could
// possibly be merged into it. I'm leaving as a separate file now in case it does
// end up diverging greatly
export default function ReactFormEditor() {
  const params = useParams();
  const [showFileNameEditor, setShowFileNameEditor] = useState(false);
  const [newFileName, setNewFileName] = useState('');
  const searchParams = useSearchParams()[0];
  const handleShowFileNameEditor = () => setShowFileNameEditor(true);
  const navigate = useNavigate();

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

  const editorDefaultLanguage = fileExtension === 'md' ? 'markdown' : 'json';

  const modifiedProcessModelId = modifyProcessModelPath(
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
    if (!params.file_name) {
      const fileNameWithExtension = `${newFileName}.${fileExtension}`;
      navigate(
        `/admin/process-models/${modifiedProcessModelId}/form/${fileNameWithExtension}`
      );
    }
  };

  const saveFile = () => {
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

  if (processModelFile || !params.file_name) {
    const processModelFileName = processModelFile ? processModelFile.name : '';
    return (
      <main>
        <ProcessBreadcrumb
          hotCrumbs={[
            ['Process Groups', '/admin'],
            [
              `Process Model: ${unModifyProcessModelPath(
                params.process_model_id || ''
              )}`,
              `process_model:${unModifyProcessModelPath(
                params.process_model_id || ''
              )}:link`,
            ],
            [processModelFileName],
          ]}
        />
        <h1>
          Process Model File{processModelFile ? ': ' : ''}
          {processModelFileName}
        </h1>
        {newFileNameBox()}
        <Button onClick={saveFile} variant="danger" data-qa="file-save-button">
          Save
        </Button>
        {params.file_name ? null : (
          <Button
            onClick={() =>
              navigate(
                `/admin/process-models/${params.process_model_id}/form-builder`
              )
            }
            variant="danger"
            data-qa="form-builder-button"
          >
            Form Builder
          </Button>
        )}
        {params.file_name ? (
          <ButtonWithConfirmation
            data-qa="delete-process-model-file"
            description={`Delete file ${params.file_name}?`}
            onConfirmation={deleteFile}
            buttonLabel="Delete"
          />
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
