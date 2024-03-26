/* eslint-disable sonarjs/cognitive-complexity */

import { useEffect, useState } from 'react';
import Editor from '@monaco-editor/react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
// @ts-ignore
import { Button, ButtonSet, Modal } from '@carbon/react';
import { Can } from '@casl/react';
import MDEditor from '@uiw/react-md-editor';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import HttpService from '../services/HttpService';
import ButtonWithConfirmation from '../components/ButtonWithConfirmation';
import { modifyProcessIdentifierForPathParam, setPageTitle } from '../helpers';
import { ProcessFile, PermissionsToCheck, ProcessModel } from '../interfaces';
import { Notification } from '../components/Notification';
import useAPIError from '../hooks/UseApiError';
import { usePermissionFetcher } from '../hooks/PermissionService';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import ActiveUsers from '../components/ActiveUsers';
// NOTE: This is mostly the same as ProcessModelEditDiagram and if we go this route could
// possibly be merged into it. I'm leaving as a separate file now in case it does
// end up diverging greatly

export default function ReactFormEditor() {
  const params = useParams();
  const { addError, removeError } = useAPIError();
  const [showFileNameEditor, setShowFileNameEditor] = useState(false);
  const [newFileName, setNewFileName] = useState('');
  const searchParams = useSearchParams()[0];
  const handleShowFileNameEditor = () => setShowFileNameEditor(true);
  const { targetUris } = useUriListForPermissions();
  const permissionRequestData: PermissionsToCheck = {
    [targetUris.processModelShowPath]: ['PUT'],
    [targetUris.processModelFileShowPath]: ['POST', 'GET', 'PUT', 'DELETE'],
  };
  const { ability } = usePermissionFetcher(permissionRequestData);
  const navigate = useNavigate();

  const [displaySaveFileMessage, setDisplaySaveFileMessage] =
    useState<boolean>(false);

  const [processModel, setProcessModel] = useState<ProcessModel | null>(null);
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
  const defaultFileName = searchParams.get('default_file_name');

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

    HttpService.makeCallToBackend({
      path: `/process-models/${modifiedProcessModelId}?include_file_references=true`,
      successCallback: setProcessModel,
    });

    if (params.file_name) {
      HttpService.makeCallToBackend({
        path: `/process-models/${modifiedProcessModelId}/files/${params.file_name}`,
        successCallback: processResult,
      });
    }
  }, [params.file_name, modifiedProcessModelId]);

  useEffect(() => {
    if (processModelFile && processModel) {
      setPageTitle([processModel.display_name, processModelFile.name]);
    }
  }, [processModel, processModelFile]);

  const navigateToProcessModelFile = (file: ProcessFile) => {
    setDisplaySaveFileMessage(true);
    if (file.file_contents_hash) {
      setProcessModelFile(file);
    }
    if (!params.file_name) {
      const fileNameWithExtension =
        defaultFileName ?? `${newFileName}.${fileExtension}`;
      navigate(
        `/process-models/${modifiedProcessModelId}/form/${fileNameWithExtension}`
      );
    }
  };

  const saveFile = () => {
    removeError();
    setDisplaySaveFileMessage(false);

    let url = `/process-models/${modifiedProcessModelId}/files`;
    let httpMethod = 'PUT';
    let fileNameWithExtension = params.file_name || defaultFileName;

    if (newFileName) {
      fileNameWithExtension = `${newFileName}.${fileExtension}`;
      httpMethod = 'POST';
    } else {
      url += `/${fileNameWithExtension}`;
      if (processModelFile && processModelFile.file_contents_hash) {
        url += `?file_contents_hash=${processModelFile.file_contents_hash}`;
      }
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
      failureCallback: addError,
      httpMethod,
      postBody: formData,
    });
  };

  const deleteFile = () => {
    const url = `/process-models/${modifiedProcessModelId}/files/${params.file_name}`;
    const httpMethod = 'DELETE';

    const navigateToProcessModelShow = (_httpResult: any) => {
      navigate(`/process-models/${modifiedProcessModelId}`);
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
            id="process_model_file_name"
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

  const editorArea = () => {
    if (fileExtension === 'md') {
      return (
        <div data-color-mode="light">
          <MDEditor
            height={600}
            highlightEnable={false}
            value={processModelFileContents || ''}
            onChange={(value) => setProcessModelFileContents(value || '')}
          />
        </div>
      );
    }
    return (
      <Editor
        height={600}
        width="auto"
        defaultLanguage={editorDefaultLanguage}
        defaultValue={processModelFileContents || ''}
        onChange={(value) => setProcessModelFileContents(value || '')}
      />
    );
  };

  if (processModelFile || !params.file_name) {
    const processModelFileName = processModelFile ? processModelFile.name : '';
    return (
      <main>
        <ProcessBreadcrumb
          hotCrumbs={[
            ['Process Groups', '/process-groups'],
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

        <ButtonSet>
          <Can
            I="PUT"
            a={targetUris.processModelFileShowPath}
            ability={ability}
          >
            <Button
              onClick={saveFile}
              variant="danger"
              data-qa="file-save-button"
            >
              Save
            </Button>
          </Can>
          <Can
            I="DELETE"
            a={targetUris.processModelFileShowPath}
            ability={ability}
          >
            {params.file_name ? (
              <ButtonWithConfirmation
                data-qa="delete-process-model-file"
                description={`Delete file ${params.file_name}?`}
                onConfirmation={deleteFile}
                buttonLabel="Delete"
              />
            ) : null}
          </Can>
          <Can
            I="GET"
            a={targetUris.processModelFileShowPath}
            ability={ability}
          >
            {hasDiagram ? (
              <Button
                onClick={() =>
                  navigate(
                    `/editor/process-models/${modifiedProcessModelId}/files/${params.file_name}`
                  )
                }
                variant="danger"
                data-qa="view-diagram-button"
              >
                View Diagram
              </Button>
            ) : null}
          </Can>
          <Can
            I="PUT"
            a={targetUris.processModelFileShowPath}
            ability={ability}
          >
            <ActiveUsers />
          </Can>
        </ButtonSet>
        {editorArea()}
      </main>
    );
  }
  return <main />;
}
