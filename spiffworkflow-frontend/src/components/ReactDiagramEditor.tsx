import React, { useRef, useState } from 'react';
import { Button, Box } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

// Import from the extracted package
import {
  BpmnEditor,
  BpmnEditorRef,
  DiagramActionBar,
  DiagramZoomControls,
  ProcessReferencesDialog,
  DiagramNavigationBreadcrumbs,
} from '../../packages/bpmn-js-spiffworkflow-react/src';
import type { DiagramNavigationItem } from '../../packages/bpmn-js-spiffworkflow-react/src';

import { modifyProcessIdentifierForPathParam } from '../helpers';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import {
  PermissionsToCheck,
  ProcessModel,
  ProcessReference,
  BasicTask,
} from '../interfaces';
import { usePermissionFetcher } from '../hooks/PermissionService';
import ProcessInstanceRun from './ProcessInstanceRun';
import ConfirmButton from './ConfirmButton';
import { TASK_METADATA } from '../config';
import { spiffBpmnApiService } from '../services/SpiffBpmnApiService';

type OwnProps = {
  modifiedProcessModelId: string;
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
  navigationStack?: DiagramNavigationItem[];
  onNavigate?: (index: number) => void;
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
  modifiedProcessModelId,
  saveDiagram,
  tasks,
  url,
  navigationStack,
  onNavigate,
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
        downloadFileName = `${modifiedProcessModelId}.${diagramType}`;
      }
      const objectUrl = URL.createObjectURL(file);
      element.href = objectUrl;
      element.download = downloadFileName;
      document.body.appendChild(element);
      element.click();

      // Clean up: revoke URL and remove element after download starts
      setTimeout(() => {
        URL.revokeObjectURL(objectUrl);
        document.body.removeChild(element);
      }, 100);
    }
  };

  const viewXml = () => {
    navigate(`/process-models/${modifiedProcessModelId}/form/${fileName}`);
  };

  const canViewXml = fileName !== undefined;

  const showReferences = () => {
    if (!callers) {
      return null;
    }
    return (
      <ProcessReferencesDialog
        open={showingReferences}
        onClose={() => setShowingReferences(false)}
        title={t('diagram_process_model_references')}
        references={callers}
        buildHref={(ref) =>
          `/process-models/${modifyProcessIdentifierForPathParam(
            ref.relative_location,
          )}`
        }
      />
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
    if (diagramType === 'readonly') {
      return null;
    }

    const deleteButton =
      fileName && !isPrimaryFile ? (
        <ConfirmButton
          description={t('delete_file_description', { file: fileName })}
          onConfirmation={handleDelete}
          buttonLabel={t('delete')}
        />
      ) : null;

    const processInstanceRun = processModel ? (
      <ProcessInstanceRun processModel={processModel} />
    ) : null;

    return (
      <DiagramActionBar
        canSave={ability.can('PUT', targetUris.processModelFileShowPath)}
        onSave={handleSave}
        saveDisabled={disableSaveButton}
        saveLabel={t('save')}
        canDelete={ability.can('DELETE', targetUris.processModelFileShowPath)}
        deleteButton={deleteButton}
        canSetPrimary={
          !!onSetPrimaryFile &&
          !isPrimaryFile &&
          ability.can('PUT', targetUris.processModelShowPath)
        }
        onSetPrimary={handleSetPrimaryFile}
        setPrimaryLabel={t('diagram_set_as_primary_file')}
        referencesButton={getReferencesButton()}
        processInstanceRun={processInstanceRun}
        activeUserElement={
          ability.can('PUT', targetUris.processModelFileShowPath)
            ? activeUserElement
            : null
        }
      />
    );
  };

  const diagramControlButtons = () => {
    return (
      <DiagramZoomControls
        onZoomIn={() => zoom(1)}
        onZoomOut={() => zoom(-1)}
        onZoomFit={() => zoom(0)}
        zoomInLabel={t('diagram_zoom_in')}
        zoomOutLabel={t('diagram_zoom_out')}
        zoomFitLabel={t('diagram_zoom_fit')}
      />
    );
  };

  return (
    <>
      <Box
        className="process-model-header"
        sx={{
          display: 'flex',
          flexWrap: 'wrap',
          rowGap: 2,
          alignItems: 'center',
          justifyContent: 'space-between',
          p: 1,
          borderBottom: 1,
          borderColor: 'divider',
          backgroundColor: 'background.paper',
        }}
        data-testid="process-model-file-show"
        data-filename={fileName}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {navigationStack && onNavigate && (
            <DiagramNavigationBreadcrumbs
              stack={navigationStack}
              onNavigate={onNavigate}
              onDownload={downloadXmlFile}
              onViewXml={viewXml}
              canDownload={ability.can(
                'GET',
                targetUris.processModelFileShowPath,
              )}
              canViewXml={
                canViewXml &&
                ability.can('GET', targetUris.processModelFileShowPath)
              }
              downloadLabel={t('diagram_download')}
              viewXmlLabel={t('diagram_view_xml')}
            />
          )}
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <div
            className="diagram-toolbar__right"
            style={{ position: 'static', transform: 'none' }}
          >
            {diagramControlButtons()}
          </div>
          <div
            className="diagram-toolbar__left"
            style={{ position: 'static', padding: 0 }}
          >
            {userActionOptions()}
          </div>
        </Box>
      </Box>
      {showReferences()}
      <BpmnEditor
        key={`${modifiedProcessModelId}-${fileName || 'new'}-${diagramType}`}
        ref={bpmnEditorRef}
        apiService={spiffBpmnApiService}
        modifiedProcessModelId={modifiedProcessModelId}
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
