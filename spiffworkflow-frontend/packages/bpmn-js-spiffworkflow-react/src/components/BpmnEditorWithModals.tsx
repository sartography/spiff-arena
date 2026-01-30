import React, { forwardRef } from 'react';
import BpmnEditor, { BpmnEditorRef } from './BpmnEditor';
import { useBpmnEditorModals } from '../hooks/useBpmnEditorModals';
import { useBpmnEditorCallbacks } from '../hooks/useBpmnEditorCallbacks';
import type { BpmnEditorProps, ProcessModel } from '../types';
import type { BpmnApiService } from '../services/BpmnApiService';
import type {
  ProcessReference,
  UseBpmnEditorModalsOptions,
} from '../hooks/useBpmnEditorModals';

// Import the modal components
import {
  ScriptEditorModal,
  MarkdownEditorModal,
  MessageEditorModal,
  JsonSchemaEditorModal,
  ProcessSearchModal,
} from './modals';

export interface BpmnEditorWithModalsProps extends Omit<
  BpmnEditorProps,
  'apiService'
> {
  /** API service for loading diagrams and fetching data */
  apiService: BpmnApiService;

  /** Process model information */
  processModel?: ProcessModel | null;

  /** Available processes for navigation/search */
  processes?: ProcessReference[];

  /** Callback to refresh processes list */
  onRefreshProcesses?: (
    callback?: (processes: ProcessReference[]) => void,
  ) => void;

  /** Callback to navigate to a path */
  onNavigate?: (path: string, newTab?: boolean) => void;

  /** External URL for JSON schema editor (optional, opens in new window) */
  externalJsonSchemaEditorUrl?: string;

  /** Callback when messages should be refreshed */
  onRefreshMessages?: (event: any) => void;

  /** Callback to add new files that don't exist */
  onAddNewFilesIfNotExist?: (fileName: string) => void;

  /** Can user access messages API */
  canAccessMessages?: boolean;

  /** Path to message model list API */
  messageModelListPath?: string;

  // Optional custom components for modals
  /** Custom Script Editor component */
  renderScriptEditor?: (props: {
    isOpen: boolean;
    script: string;
    scriptType: string;
    onClose: () => void;
    onScriptChange: (script: string) => void;
  }) => React.ReactNode;

  /** Custom Markdown Editor component */
  renderMarkdownEditor?: (props: {
    isOpen: boolean;
    markdown: string;
    onClose: () => void;
    onMarkdownChange: (markdown: string) => void;
  }) => React.ReactNode;

  /** Custom Message Editor component (passed as children to modal) */
  messageEditorChildren?: React.ReactNode;

  /** Custom JSON Schema Editor component (passed as children to modal) */
  jsonSchemaEditorChildren?: React.ReactNode;

  /** Custom Process Search component (passed as children to modal) */
  processSearchChildren?: React.ReactNode;
}

/**
 * Comprehensive BPMN editor component that includes built-in modal management and UI.
 *
 * This component provides a complete out-of-the-box BPMN editing experience with:
 * - Script editor with Monaco Editor
 * - Markdown editor with MDEditor
 * - Message editor modal
 * - JSON schema editor modal
 * - Process search modal
 *
 * All modals can be customized by providing custom components via props.
 *
 * @example
 * ```tsx
 * // Simple usage with defaults
 * <BpmnEditorWithModals
 *   apiService={myApiService}
 *   processModelId="my-process"
 *   diagramType="bpmn"
 *   processModel={processModel}
 *   processes={processes}
 * />
 * ```
 */
const BpmnEditorWithModals = forwardRef<
  BpmnEditorRef,
  BpmnEditorWithModalsProps
>(
  (
    {
      apiService,
      processModel,
      processes = [],
      onRefreshProcesses,
      onNavigate,
      externalJsonSchemaEditorUrl,
      onRefreshMessages,
      onAddNewFilesIfNotExist,
      canAccessMessages = false,
      messageModelListPath,
      renderScriptEditor,
      renderMarkdownEditor,
      messageEditorChildren,
      jsonSchemaEditorChildren,
      processSearchChildren,
      // BpmnEditor props
      modifiedProcessModelId,
      diagramType,
      ...bpmnEditorProps
    },
    ref,
  ) => {
    // Set up modal management
    const modalOptions: UseBpmnEditorModalsOptions = {
      processModel,
      processes,
      onRefreshProcesses,
      onNavigate,
      externalJsonSchemaEditorUrl,
      processModelId: modifiedProcessModelId,
      onRefreshMessages,
      onAddNewFilesIfNotExist,
    };

    const [modalStates, modalActions] = useBpmnEditorModals(modalOptions);

    // Set up API-based callbacks
    const bpmnEditorCallbacks = useBpmnEditorCallbacks({
      apiService,
      processModel,
      canAccessMessages,
      messageModelListPath,
    });

    return (
      <>
        <BpmnEditor
          ref={ref}
          apiService={apiService}
          modifiedProcessModelId={modifiedProcessModelId}
          diagramType={diagramType}
          {...bpmnEditorProps}
          // Hook up modal actions
          onLaunchScriptEditor={modalActions.openScriptEditor}
          onLaunchMarkdownEditor={modalActions.openMarkdownEditor}
          onLaunchMessageEditor={modalActions.openMessageEditor}
          onLaunchJsonSchemaEditor={modalActions.openJsonSchemaEditor}
          onSearchProcessModels={modalActions.openProcessSearch}
          onLaunchBpmnEditor={modalActions.navigateToBpmnEditor}
          onLaunchDmnEditor={modalActions.navigateToDmnEditor}
          // Hook up API callbacks
          onDataStoresRequested={bpmnEditorCallbacks.onDataStoresRequested}
          onDmnFilesRequested={bpmnEditorCallbacks.onDmnFilesRequested}
          onJsonSchemaFilesRequested={
            bpmnEditorCallbacks.onJsonSchemaFilesRequested
          }
          onMessagesRequested={bpmnEditorCallbacks.onMessagesRequested}
          onServiceTasksRequested={bpmnEditorCallbacks.onServiceTasksRequested}
        />

        {/* Render modals using custom or default components */}
        {renderScriptEditor ? (
          renderScriptEditor({
            isOpen: modalStates.scriptEditor.isOpen,
            script: modalStates.scriptEditor.script,
            scriptType: modalStates.scriptEditor.scriptType,
            onClose: modalActions.closeScriptEditor,
            onScriptChange: modalActions.updateScriptEditorScript,
          })
        ) : (
          <ScriptEditorModal
            isOpen={modalStates.scriptEditor.isOpen}
            script={modalStates.scriptEditor.script}
            scriptType={modalStates.scriptEditor.scriptType}
            scriptName={
              modalStates.scriptEditor.element?.di?.bpmnElement?.name ||
              'Script'
            }
            onClose={modalActions.closeScriptEditor}
            onScriptChange={modalActions.updateScriptEditorScript}
          />
        )}

        {renderMarkdownEditor ? (
          renderMarkdownEditor({
            isOpen: modalStates.markdownEditor.isOpen,
            markdown: modalStates.markdownEditor.markdown,
            onClose: modalActions.closeMarkdownEditor,
            onMarkdownChange: (md: string) =>
              modalActions.updateMarkdownEditorContent(md),
          })
        ) : (
          <MarkdownEditorModal
            isOpen={modalStates.markdownEditor.isOpen}
            markdown={modalStates.markdownEditor.markdown}
            onClose={modalActions.closeMarkdownEditor}
            onMarkdownChange={modalActions.updateMarkdownEditorContent}
          />
        )}

        <MessageEditorModal
          isOpen={modalStates.messageEditor.isOpen}
          messageId={modalStates.messageEditor.messageId}
          elementId={modalStates.messageEditor.elementId}
          correlationProperties={
            modalStates.messageEditor.correlationProperties
          }
          event={modalStates.messageEditor.event}
          onClose={modalActions.closeMessageEditor}
          onSave={() => {
            if (modalStates.messageEditor.event) {
              modalStates.messageEditor.event.eventBus.fire(
                'spiff.message.save',
              );
            }
          }}
        >
          {messageEditorChildren}
        </MessageEditorModal>

        <JsonSchemaEditorModal
          isOpen={modalStates.jsonSchemaEditor.isOpen}
          fileName={modalStates.jsonSchemaEditor.fileName}
          onClose={modalActions.closeJsonSchemaEditor}
          onFileNameChange={modalActions.updateJsonSchemaFileName}
        >
          {jsonSchemaEditorChildren}
        </JsonSchemaEditorModal>

        <ProcessSearchModal
          isOpen={modalStates.processSearch.isOpen}
          processes={processes}
          onClose={modalActions.closeProcessSearch}
        >
          {processSearchChildren}
        </ProcessSearchModal>
      </>
    );
  },
);

BpmnEditorWithModals.displayName = 'BpmnEditorWithModals';

export default BpmnEditorWithModals;
