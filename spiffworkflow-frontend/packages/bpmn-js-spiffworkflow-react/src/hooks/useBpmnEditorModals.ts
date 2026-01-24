import { useState, useCallback } from 'react';

export interface ProcessReference {
  identifier: string;
  relative_location: string;
  file_name: string;
  display_name: string;
}

export interface ProcessFile {
  name: string;
  type: string;
  references: Array<{
    identifier: string;
    display_name: string;
  }>;
}

export interface ProcessModel {
  id: string;
  files?: ProcessFile[];
}

export interface ScriptEditorModalState {
  isOpen: boolean;
  element: any;
  script: string;
  scriptType: string;
  eventBus: any;
  modeling: any;
}

export interface MarkdownEditorModalState {
  isOpen: boolean;
  element: any;
  markdown: string;
  eventBus: any;
}

export interface MessageEditorModalState {
  isOpen: boolean;
  event: any;
  messageId: string;
  elementId: string;
  correlationProperties: any;
}

export interface JsonSchemaEditorModalState {
  isOpen: boolean;
  element: any;
  fileName: string;
  eventBus: any;
}

export interface ProcessSearchModalState {
  isOpen: boolean;
  processId: string;
  eventBus: any;
  element: any;
}

export interface UseBpmnEditorModalsOptions {
  /** Process model for file lookups */
  processModel?: ProcessModel | null;

  /** Available processes for BPMN editor navigation */
  processes?: ProcessReference[];

  /** Callback to refresh processes list */
  onRefreshProcesses?: (callback?: (processes: ProcessReference[]) => void) => void;

  /** Callback to navigate to a path */
  onNavigate?: (path: string, newTab?: boolean) => void;

  /** External URL for JSON schema editor (optional) */
  externalJsonSchemaEditorUrl?: string;

  /** Current process model ID for external editor URL */
  processModelId?: string;

  /** Callback when messages should be refreshed */
  onRefreshMessages?: (event: any) => void;

  /** Callback to add new files that don't exist */
  onAddNewFilesIfNotExist?: (fileName: string) => void;
}

export interface BpmnEditorModalsState {
  scriptEditor: ScriptEditorModalState;
  markdownEditor: MarkdownEditorModalState;
  messageEditor: MessageEditorModalState;
  jsonSchemaEditor: JsonSchemaEditorModalState;
  processSearch: ProcessSearchModalState;
}

export interface BpmnEditorModalsActions {
  // Script Editor
  openScriptEditor: (
    element: any,
    script: string,
    scriptType: string,
    eventBus: any,
    modeling: any
  ) => void;
  closeScriptEditor: () => void;
  updateScriptEditorScript: (script: string) => void;

  // Markdown Editor
  openMarkdownEditor: (element: any, markdown: string, eventBus: any) => void;
  closeMarkdownEditor: () => void;
  updateMarkdownEditorContent: (markdown: string) => void;

  // Message Editor
  openMessageEditor: (event: any) => void;
  closeMessageEditor: () => void;

  // JSON Schema Editor
  openJsonSchemaEditor: (element: any, fileName: string, eventBus: any) => void;
  closeJsonSchemaEditor: () => void;
  updateJsonSchemaFileName: (fileName: string) => void;

  // Process Search
  openProcessSearch: (processId: string, eventBus: any, element: any) => void;
  closeProcessSearch: (selection?: ProcessReference | null) => void;

  // Navigation
  navigateToBpmnEditor: (processId: string) => void;
  navigateToDmnEditor: (processId: string) => void;
}

/**
 * Comprehensive hook for managing all BPMN editor modal states and logic.
 * Handles script editor, markdown editor, message editor, JSON schema editor, and process search.
 *
 * @example
 * ```tsx
 * const [modalStates, modalActions] = useBpmnEditorModals({
 *   processModel,
 *   processes,
 *   onNavigate: (path, newTab) => newTab ? window.open(path) : navigate(path),
 * });
 *
 * // Use with BpmnEditor
 * <BpmnEditor
 *   onLaunchScriptEditor={modalActions.openScriptEditor}
 *   onLaunchMarkdownEditor={modalActions.openMarkdownEditor}
 *   {...otherProps}
 * />
 *
 * // Render modals based on state
 * {modalStates.scriptEditor.isOpen && (
 *   <ScriptEditorDialog
 *     script={modalStates.scriptEditor.script}
 *     onClose={modalActions.closeScriptEditor}
 *   />
 * )}
 * ```
 */
export function useBpmnEditorModals(
  options: UseBpmnEditorModalsOptions
): [BpmnEditorModalsState, BpmnEditorModalsActions] {
  const {
    processModel,
    processes = [],
    onRefreshProcesses,
    onNavigate,
    externalJsonSchemaEditorUrl,
    processModelId,
    onRefreshMessages,
    onAddNewFilesIfNotExist,
  } = options;

  // Script Editor State
  const [scriptEditorState, setScriptEditorState] = useState<ScriptEditorModalState>({
    isOpen: false,
    element: null,
    script: '',
    scriptType: '',
    eventBus: null,
    modeling: null,
  });

  // Markdown Editor State
  const [markdownEditorState, setMarkdownEditorState] = useState<MarkdownEditorModalState>({
    isOpen: false,
    element: null,
    markdown: '',
    eventBus: null,
  });

  // Message Editor State
  const [messageEditorState, setMessageEditorState] = useState<MessageEditorModalState>({
    isOpen: false,
    event: null,
    messageId: '',
    elementId: '',
    correlationProperties: null,
  });

  // JSON Schema Editor State
  const [jsonSchemaEditorState, setJsonSchemaEditorState] = useState<JsonSchemaEditorModalState>({
    isOpen: false,
    element: null,
    fileName: '',
    eventBus: null,
  });

  // Process Search State
  const [processSearchState, setProcessSearchState] = useState<ProcessSearchModalState>({
    isOpen: false,
    processId: '',
    eventBus: null,
    element: null,
  });

  // Script Editor Actions
  const openScriptEditor = useCallback(
    (element: any, script: string, scriptType: string, eventBus: any, modeling: any) => {
      setScriptEditorState({
        isOpen: true,
        element,
        script: script || '',
        scriptType,
        eventBus,
        modeling,
      });
    },
    []
  );

  const closeScriptEditor = useCallback(() => {
    if (scriptEditorState.eventBus) {
      scriptEditorState.eventBus.fire('spiff.script.update', {
        scriptType: scriptEditorState.scriptType,
        script: scriptEditorState.script,
        element: scriptEditorState.element,
      });
    }
    setScriptEditorState({
      isOpen: false,
      element: null,
      script: '',
      scriptType: '',
      eventBus: null,
      modeling: null,
    });
  }, [scriptEditorState]);

  const updateScriptEditorScript = useCallback((script: string) => {
    setScriptEditorState((prev) => ({ ...prev, script }));
  }, []);

  // Markdown Editor Actions
  const openMarkdownEditor = useCallback(
    (element: any, markdown: string, eventBus: any) => {
      setMarkdownEditorState({
        isOpen: true,
        element,
        markdown: markdown || '',
        eventBus,
      });
    },
    []
  );

  const closeMarkdownEditor = useCallback(() => {
    if (markdownEditorState.eventBus) {
      markdownEditorState.eventBus.fire('spiff.markdown.update', {
        value: markdownEditorState.markdown,
      });
    }
    setMarkdownEditorState({
      isOpen: false,
      element: null,
      markdown: '',
      eventBus: null,
    });
  }, [markdownEditorState]);

  const updateMarkdownEditorContent = useCallback((markdown: string) => {
    setMarkdownEditorState((prev) => ({ ...prev, markdown }));
  }, []);

  // Message Editor Actions
  const openMessageEditor = useCallback((event: any) => {
    setMessageEditorState({
      isOpen: true,
      event,
      messageId: event.value?.messageId || '',
      elementId: event.value?.elementId || '',
      correlationProperties: event.value?.correlation_properties || null,
    });
  }, []);

  const closeMessageEditor = useCallback(() => {
    if (messageEditorState.event && onRefreshMessages) {
      onRefreshMessages(messageEditorState.event);
    }
    setMessageEditorState({
      isOpen: false,
      event: null,
      messageId: '',
      elementId: '',
      correlationProperties: null,
    });
  }, [messageEditorState, onRefreshMessages]);

  // JSON Schema Editor Actions
  const openJsonSchemaEditor = useCallback(
    (element: any, fileName: string, eventBus: any) => {
      // If external editor URL is configured, open it
      if (externalJsonSchemaEditorUrl) {
        const url = `${externalJsonSchemaEditorUrl}?processModelId=${processModelId || ''}&fileName=${fileName || ''}`;
        window.open(url, '_blank');
        return;
      }

      setJsonSchemaEditorState({
        isOpen: true,
        element,
        fileName,
        eventBus,
      });
    },
    [externalJsonSchemaEditorUrl, processModelId]
  );

  const closeJsonSchemaEditor = useCallback(() => {
    if (onAddNewFilesIfNotExist && jsonSchemaEditorState.fileName) {
      onAddNewFilesIfNotExist(jsonSchemaEditorState.fileName);
    }
    if (jsonSchemaEditorState.eventBus) {
      jsonSchemaEditorState.eventBus.fire('spiff.jsonSchema.update', {
        value: jsonSchemaEditorState.fileName,
      });
    }
    setJsonSchemaEditorState({
      isOpen: false,
      element: null,
      fileName: '',
      eventBus: null,
    });
  }, [jsonSchemaEditorState, onAddNewFilesIfNotExist]);

  const updateJsonSchemaFileName = useCallback((fileName: string) => {
    setJsonSchemaEditorState((prev) => ({ ...prev, fileName }));
  }, []);

  // Process Search Actions
  const openProcessSearch = useCallback(
    (processId: string, eventBus: any, element: any) => {
      setProcessSearchState({
        isOpen: true,
        processId,
        eventBus,
        element,
      });
    },
    []
  );

  const closeProcessSearch = useCallback(
    (selection?: ProcessReference | null) => {
      if (selection && processSearchState.eventBus) {
        processSearchState.eventBus.fire('spiff.callactivity.update', {
          element: processSearchState.element,
          value: selection.identifier,
        });
      }
      setProcessSearchState({
        isOpen: false,
        processId: '',
        eventBus: null,
        element: null,
      });
    },
    [processSearchState]
  );

  // Helper to find file by reference ID
  const findFileForReference = useCallback(
    (processId: string, fileType: string): ProcessFile | null => {
      if (!processModel?.files) {
        return null;
      }
      const files = processModel.files.filter((f) => f.type === fileType);
      let matchFile = null;
      files.some((file) => {
        if (file.references.some((ref) => ref.identifier === processId)) {
          matchFile = file;
          return true;
        }
        return false;
      });
      return matchFile as ProcessFile | null;
    },
    [processModel]
  );

  // BPMN Editor Navigation
  const navigateToBpmnEditor = useCallback(
    (processId: string) => {
      if (!onNavigate) {
        console.warn('onNavigate not configured for BPMN editor navigation');
        return;
      }

      const openProcessFile = (processRef: ProcessReference) => {
        // Construct the path - application should handle path construction
        // For now, we'll pass a generic format
        onNavigate(
          `/process-models/${processRef.relative_location}/files/${processRef.file_name}`,
          true // open in new tab
        );
      };

      const openFileForProcessId = (processRefs: ProcessReference[]) => {
        const processRef = processRefs.find((p) => p.identifier === processId);
        if (processRef) {
          openProcessFile(processRef);
        }
      };

      // Check if process exists in current list
      const processRef = processes.find((p) => p.identifier === processId);
      if (!processRef && onRefreshProcesses) {
        // Refresh and try again
        onRefreshProcesses(openFileForProcessId);
      } else if (processRef) {
        openProcessFile(processRef);
      }
    },
    [processes, onNavigate, onRefreshProcesses]
  );

  // DMN Editor Navigation
  const navigateToDmnEditor = useCallback(
    (processId: string) => {
      if (!onNavigate) {
        console.warn('onNavigate not configured for DMN editor navigation');
        return;
      }

      const file = findFileForReference(processId, 'dmn');
      if (file) {
        onNavigate(`/process-models/${processModelId}/files/${file.name}`, true);
      } else {
        // No file found, navigate to create DMN file
        onNavigate(`/process-models/${processModelId}/files?file_type=dmn`, true);
      }
    },
    [findFileForReference, onNavigate, processModelId]
  );

  const state: BpmnEditorModalsState = {
    scriptEditor: scriptEditorState,
    markdownEditor: markdownEditorState,
    messageEditor: messageEditorState,
    jsonSchemaEditor: jsonSchemaEditorState,
    processSearch: processSearchState,
  };

  const actions: BpmnEditorModalsActions = {
    openScriptEditor,
    closeScriptEditor,
    updateScriptEditorScript,
    openMarkdownEditor,
    closeMarkdownEditor,
    updateMarkdownEditorContent,
    openMessageEditor,
    closeMessageEditor,
    openJsonSchemaEditor,
    closeJsonSchemaEditor,
    updateJsonSchemaFileName,
    openProcessSearch,
    closeProcessSearch,
    navigateToBpmnEditor,
    navigateToDmnEditor,
  };

  return [state, actions];
}
