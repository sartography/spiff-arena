import React, { useRef, useState } from 'react';
import { Modal, UnorderedList, Link } from '@carbon/react';
import { Button, IconButton, Stack } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Can } from '@casl/react';
import {
  ZoomIn,
  ZoomOut,
  CenterFocusStrongOutlined,
} from '@mui/icons-material';

// Import from the extracted package
import { BpmnEditor, BpmnEditorRef } from '../../packages/bpmn-js-spiffworkflow-react/src';

import { modifyProcessIdentifierForPathParam } from '../helpers';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import {
  PermissionsToCheck,
  ProcessModel,
  ProcessReference,
  BasicTask,
} from '../interfaces';
import { usePermissionFetcher } from '../hooks/PermissionService';
import SpiffTooltip from './SpiffTooltip';
import ProcessInstanceRun from './ProcessInstanceRun';
import ConfirmButton from './ConfirmButton';
import { TASK_METADATA } from '../config';
import { spiffBpmnApiService } from '../services/SpiffBpmnApiService';

type OwnProps = {
  processModelId: string;
  diagramType: string;
  activeUserElement?: React.ReactElement;
  callers?: ProcessReference[];
  diagramXML?: string | null;
  disableSaveButton?: boolean;
  fileName?: string;
  isPrimaryFile?: boolean;
  processModel?: ProcessModel | null;
  onCallActivityOverlayClick?: (..._args: any[]) => any;
  onDataStoresRequested?: (..._args: any[]) => any;
  onDeleteFile?: (..._args: any[]) => any;
  onDmnFilesRequested?: (..._args: any[]) => any;
  onElementClick?: (..._args: any[]) => any;
  onElementsChanged?: (..._args: any[]) => any;
  onJsonSchemaFilesRequested?: (..._args: any[]) => any;
  onLaunchBpmnEditor?: (..._args: any[]) => any;
  onLaunchDmnEditor?: (..._args: any[]) => any;
  onLaunchJsonSchemaEditor?: (..._args: any[]) => any;
  onLaunchMarkdownEditor?: (..._args: any[]) => any;
  onLaunchScriptEditor?: (..._args: any[]) => any;
  onLaunchMessageEditor?: (..._args: any[]) => any;
  onMessagesRequested?: (..._args: any[]) => any;
  onSearchProcessModels?: (..._args: any[]) => any;
  onServiceTasksRequested?: (..._args: any[]) => any;
  onSetPrimaryFile?: (..._args: any[]) => any;
  saveDiagram?: (..._args: any[]) => any;
  tasks?: BasicTask[] | null;
  url?: string;
};

export default function ReactDiagramEditor({
  activeUserElement,
  callers,
  diagramType,
  diagramXML,
  disableSaveButton,
  fileName,
  isPrimaryFile,
  processModel,
  onCallActivityOverlayClick,
  onDataStoresRequested,
  onDeleteFile,
  onDmnFilesRequested,
  onElementClick,
  onElementsChanged,
  onJsonSchemaFilesRequested,
  onLaunchBpmnEditor,
  onLaunchDmnEditor,
  onLaunchJsonSchemaEditor,
  onLaunchMarkdownEditor,
  onLaunchScriptEditor,
  onLaunchMessageEditor,
  onMessagesRequested,
  onSearchProcessModels,
  onServiceTasksRequested,
  onSetPrimaryFile,
  processModelId,
  saveDiagram,
  tasks,
  url,
}: OwnProps) {
  const bpmnEditorRef = useRef<BpmnEditorRef>(null);
  const [showingReferences, setShowingReferences] = useState(false);

  const { targetUris } = useUriListForPermissions();
  const permissionRequestData: PermissionsToCheck = {};

  if (diagramType !== 'readonly') {
    permissionRequestData[targetUris.processModelShowPath] = ['PUT'];
    permissionRequestData[targetUris.processModelFileShowPath] = [
      'POST',
      'GET',
      'PUT',
      'DELETE',
    ];
  }

  const { ability } = usePermissionFetcher(permissionRequestData);
  const navigate = useNavigate();
  const { t } = useTranslation();

  const zoom = (amount: number) => {
    bpmnEditorRef.current?.zoom(amount);
  };

  async function handleSave() {
    if (saveDiagram && bpmnEditorRef.current) {
      const xml = await bpmnEditorRef.current.getXML();
      saveDiagram(xml);
    }
  }

  function handleDelete() {
    if (onDeleteFile) {
      onDeleteFile(fileName);
    }
  }

  function handleSetPrimaryFile() {
    if (onSetPrimaryFile) {
      onSetPrimaryFile(fileName);
    }
  }

  const downloadXmlFile = async () => {
    if (bpmnEditorRef.current) {
      const xml = await bpmnEditorRef.current.getXML();
      const element = document.createElement('a');
      const file = new Blob([xml], {
        type: 'application/xml',
      });
      let downloadFileName = fileName;
      if (!downloadFileName) {
        downloadFileName = `${processModelId}.${diagramType}`;
      }
      element.href = URL.createObjectURL(file);
      element.download = downloadFileName;
      document.body.appendChild(element);
      element.click();
    }
  };

  const canViewXml = fileName !== undefined;

  const showReferences = () => {
    if (!callers) {
      return null;
    }
    return (
      <Modal
        open={showingReferences}
        modalHeading={t('diagram_process_model_references')}
        onRequestClose={() => setShowingReferences(false)}
        passiveModal
      >
        <UnorderedList>
          {callers.map((ref: ProcessReference) => (
            <li key={`list-${ref.relative_location}`}>
              <Link
                size="lg"
                href={`/process-models/${modifyProcessIdentifierForPathParam(
                  ref.relative_location,
                )}`}
              >
                {`${ref.display_name}`}
              </Link>{' '}
              ({ref.relative_location})
            </li>
          ))}
        </UnorderedList>
      </Modal>
    );
  };

  const getReferencesButton = () => {
    if (callers && callers.length > 0) {
      let buttonText = t('diagram_references_count', { count: 1 });
      if (callers.length > 1) {
        buttonText = t('diagram_references_count_plural', {
          count: callers.length,
        });
      }
      return (
        <Button variant="contained" onClick={() => setShowingReferences(true)}>
          {buttonText}
        </Button>
      );
    }
    return null;
  };

  const userActionOptions = () => {
    if (diagramType !== 'readonly') {
      return (
        <Stack sx={{ mt: 2 }} direction="row" spacing={2}>
          <Can
            I="PUT"
            a={targetUris.processModelFileShowPath}
            ability={ability}
          >
            <Button
              onClick={handleSave}
              variant="contained"
              disabled={disableSaveButton}
              data-testid="process-model-file-save-button"
            >
              {t('save')}
            </Button>
          </Can>
          {processModel && <ProcessInstanceRun processModel={processModel} />}
          <Can
            I="DELETE"
            a={targetUris.processModelFileShowPath}
            ability={ability}
          >
            {fileName && !isPrimaryFile && (
              <ConfirmButton
                description={t('delete_file_description', { file: fileName })}
                onConfirmation={handleDelete}
                buttonLabel={t('delete')}
              />
            )}
          </Can>
          <Can I="PUT" a={targetUris.processModelShowPath} ability={ability}>
            {onSetPrimaryFile && (
              <Button onClick={handleSetPrimaryFile} variant="contained">
                {t('diagram_set_as_primary_file')}
              </Button>
            )}
          </Can>
          <Can
            I="GET"
            a={targetUris.processModelFileShowPath}
            ability={ability}
          >
            <Button variant="contained" onClick={downloadXmlFile}>
              {t('diagram_download')}
            </Button>
          </Can>
          <Can
            I="GET"
            a={targetUris.processModelFileShowPath}
            ability={ability}
          >
            {canViewXml && (
              <Button
                variant="contained"
                onClick={() => {
                  navigate(
                    `/process-models/${processModelId}/form/${fileName}`,
                  );
                }}
              >
                {t('diagram_view_xml')}
              </Button>
            )}
          </Can>
          {getReferencesButton()}
          <Can
            I="PUT"
            a={targetUris.processModelFileShowPath}
            ability={ability}
          >
            {activeUserElement || null}
          </Can>
        </Stack>
      );
    }
    return null;
  };

  const diagramControlButtons = () => {
    return (
      <div className="diagram-control-buttons">
        <SpiffTooltip title={t('diagram_zoom_in')} placement="bottom">
          <IconButton aria-label={t('diagram_zoom_in')} onClick={() => zoom(1)}>
            <ZoomIn />
          </IconButton>
        </SpiffTooltip>
        <SpiffTooltip title={t('diagram_zoom_out')} placement="bottom">
          <IconButton
            aria-label={t('diagram_zoom_out')}
            onClick={() => zoom(-1)}
          >
            <ZoomOut />
          </IconButton>
        </SpiffTooltip>
        <SpiffTooltip title={t('diagram_zoom_fit')} placement="bottom">
          <IconButton
            aria-label={t('diagram_zoom_fit')}
            onClick={() => zoom(0)}
          >
            <CenterFocusStrongOutlined />
          </IconButton>
        </SpiffTooltip>
      </div>
    );
  };

  return (
    <>
      {userActionOptions()}
      {showReferences()}
      {diagramControlButtons()}
      <BpmnEditor
        ref={bpmnEditorRef}
        apiService={spiffBpmnApiService}
        processModelId={processModelId}
        diagramType={diagramType as 'bpmn' | 'dmn' | 'readonly'}
        diagramXML={diagramXML}
        fileName={fileName}
        tasks={tasks}
        url={url}
        taskMetadataKeys={TASK_METADATA}
        onCallActivityOverlayClick={onCallActivityOverlayClick}
        onDataStoresRequested={onDataStoresRequested}
        onDmnFilesRequested={onDmnFilesRequested}
        onElementClick={onElementClick}
        onElementsChanged={onElementsChanged}
        onJsonSchemaFilesRequested={onJsonSchemaFilesRequested}
        onLaunchBpmnEditor={onLaunchBpmnEditor}
        onLaunchDmnEditor={onLaunchDmnEditor}
        onLaunchJsonSchemaEditor={onLaunchJsonSchemaEditor}
        onLaunchMarkdownEditor={onLaunchMarkdownEditor}
        onLaunchScriptEditor={onLaunchScriptEditor}
        onLaunchMessageEditor={onLaunchMessageEditor}
        onMessagesRequested={onMessagesRequested}
        onSearchProcessModels={onSearchProcessModels}
        onServiceTasksRequested={onServiceTasksRequested}
      />
    </>
  );
}