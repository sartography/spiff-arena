import { useCallback } from 'react';

export interface ScriptEditorState {
  element: any;
  script: string;
  scriptType: string;
  eventBus: any;
  modeling: any;
}

export interface MarkdownEditorState {
  element: any;
  markdown: string;
  eventBus: any;
}

export interface MessageEditorState {
  event: any;
  messageId: string;
  elementId: string;
  correlationProperties: any;
}

export interface JsonSchemaEditorState {
  element: any;
  fileName: string;
  eventBus: any;
}

export interface ProcessSearchState {
  processId: string;
  eventBus: any;
  element: any;
}

export interface UseBpmnEditorLaunchersOptions {
  /**
   * Handler called when script editor should be opened
   * Application should open a modal/dialog with the script editor
   */
  onOpenScriptEditor?: (state: ScriptEditorState) => void;

  /**
   * Handler called when markdown editor should be opened
   * Application should open a modal/dialog with the markdown editor
   */
  onOpenMarkdownEditor?: (state: MarkdownEditorState) => void;

  /**
   * Handler called when message editor should be opened
   * Application should open a modal/dialog with the message editor
   */
  onOpenMessageEditor?: (state: MessageEditorState) => void;

  /**
   * Handler called when JSON schema editor should be opened
   * Application should open a modal/dialog with the JSON schema editor
   */
  onOpenJsonSchemaEditor?: (state: JsonSchemaEditorState) => void;

  /**
   * Handler called when process search should be opened
   * Application should open a modal/dialog for selecting a process
   */
  onOpenProcessSearch?: (state: ProcessSearchState) => void;

  /**
   * Handler called when a BPMN file should be opened
   * Application should navigate to or open the BPMN editor for the given process ID
   */
  onOpenBpmnEditor?: (processId: string) => void;

  /**
   * Handler called when a DMN file should be opened
   * Application should navigate to or open the DMN editor for the given process ID
   */
  onOpenDmnEditor?: (processId: string) => void;
}

export interface BpmnEditorLaunchers {
  onLaunchScriptEditor: (
    element: any,
    script: string,
    scriptType: string,
    eventBus: any,
    modeling: any
  ) => void;
  onLaunchMarkdownEditor: (element: any, markdown: string, eventBus: any) => void;
  onLaunchMessageEditor: (event: any) => void;
  onLaunchJsonSchemaEditor: (element: any, fileName: string, eventBus: any) => void;
  onSearchProcessModels: (processId: string, eventBus: any, element: any) => void;
  onLaunchBpmnEditor: (processId: string) => void;
  onLaunchDmnEditor: (processId: string) => void;
}

/**
 * Hook that provides launcher callbacks for opening editors and modals.
 * Applications implement the UI by providing handler functions that open their dialogs/modals.
 *
 * @example
 * ```tsx
 * const launchers = useBpmnEditorLaunchers({
 *   onOpenScriptEditor: (state) => {
 *     setScriptEditorState(state);
 *     setShowScriptEditor(true);
 *   },
 *   onOpenBpmnEditor: (processId) => {
 *     navigate(`/process/${processId}`);
 *   },
 * });
 *
 * <BpmnEditor
 *   {...launchers}
 * />
 * ```
 */
export function useBpmnEditorLaunchers(
  options: UseBpmnEditorLaunchersOptions
): BpmnEditorLaunchers {
  const {
    onOpenScriptEditor,
    onOpenMarkdownEditor,
    onOpenMessageEditor,
    onOpenJsonSchemaEditor,
    onOpenProcessSearch,
    onOpenBpmnEditor,
    onOpenDmnEditor,
  } = options;

  /**
   * Launch script editor with the given parameters
   */
  const onLaunchScriptEditor = useCallback(
    (
      element: any,
      script: string,
      scriptType: string,
      eventBus: any,
      modeling: any
    ) => {
      if (onOpenScriptEditor) {
        onOpenScriptEditor({
          element,
          script: script || '',
          scriptType,
          eventBus,
          modeling,
        });
      }
    },
    [onOpenScriptEditor]
  );

  /**
   * Launch markdown editor with the given parameters
   */
  const onLaunchMarkdownEditor = useCallback(
    (element: any, markdown: string, eventBus: any) => {
      if (onOpenMarkdownEditor) {
        onOpenMarkdownEditor({
          element,
          markdown: markdown || '',
          eventBus,
        });
      }
    },
    [onOpenMarkdownEditor]
  );

  /**
   * Launch message editor with the given event
   */
  const onLaunchMessageEditor = useCallback(
    (event: any) => {
      if (onOpenMessageEditor) {
        onOpenMessageEditor({
          event,
          messageId: event.value.messageId,
          elementId: event.value.elementId,
          correlationProperties: event.value.correlation_properties,
        });
      }
    },
    [onOpenMessageEditor]
  );

  /**
   * Launch JSON schema editor with the given parameters
   */
  const onLaunchJsonSchemaEditor = useCallback(
    (element: any, fileName: string, eventBus: any) => {
      if (onOpenJsonSchemaEditor) {
        onOpenJsonSchemaEditor({
          element,
          fileName,
          eventBus,
        });
      }
    },
    [onOpenJsonSchemaEditor]
  );

  /**
   * Launch process search modal
   */
  const onSearchProcessModels = useCallback(
    (processId: string, eventBus: any, element: any) => {
      if (onOpenProcessSearch) {
        onOpenProcessSearch({
          processId,
          eventBus,
          element,
        });
      }
    },
    [onOpenProcessSearch]
  );

  /**
   * Navigate to or open a BPMN editor for the given process ID
   */
  const onLaunchBpmnEditor = useCallback(
    (processId: string) => {
      if (onOpenBpmnEditor) {
        onOpenBpmnEditor(processId);
      }
    },
    [onOpenBpmnEditor]
  );

  /**
   * Navigate to or open a DMN editor for the given process ID
   */
  const onLaunchDmnEditor = useCallback(
    (processId: string) => {
      if (onOpenDmnEditor) {
        onOpenDmnEditor(processId);
      }
    },
    [onOpenDmnEditor]
  );

  return {
    onLaunchScriptEditor,
    onLaunchMarkdownEditor,
    onLaunchMessageEditor,
    onLaunchJsonSchemaEditor,
    onSearchProcessModels,
    onLaunchBpmnEditor,
    onLaunchDmnEditor,
  };
}

/**
 * Helper to fire a script update event back to bpmn-js
 * Call this when the user closes/saves the script editor
 */
export function fireScriptUpdate(
  eventBus: any,
  scriptType: string,
  script: string,
  element: any
) {
  eventBus.fire('spiff.script.update', {
    scriptType,
    script,
    element,
  });
}

/**
 * Helper to fire a markdown update event back to bpmn-js
 * Call this when the user closes/saves the markdown editor
 */
export function fireMarkdownUpdate(eventBus: any, value: string) {
  eventBus.fire('spiff.markdown.update', {
    value,
  });
}

/**
 * Helper to fire a JSON schema update event back to bpmn-js
 * Call this when the user closes/saves the JSON schema editor
 */
export function fireJsonSchemaUpdate(eventBus: any, value: string) {
  eventBus.fire('spiff.jsonSchema.update', {
    value,
  });
}

/**
 * Helper to fire a message save event back to bpmn-js
 * Call this when the user saves the message editor
 */
export function fireMessageSave(eventBus: any) {
  eventBus.fire('spiff.message.save');
}

/**
 * Helper to fire a call activity update event back to bpmn-js
 * Call this when the user selects a process model for a call activity
 */
export function fireCallActivityUpdate(
  eventBus: any,
  element: any,
  value: string
) {
  eventBus.fire('spiff.callactivity.update', {
    element,
    value,
  });
}

/**
 * Helper to close markdown editor and persist the value
 */
export function closeMarkdownEditorWithUpdate(
  eventBus: any,
  value: string,
  closeFn: () => void
) {
  fireMarkdownUpdate(eventBus, value);
  closeFn();
}

/**
 * Helper to close JSON schema editor and persist the value
 */
export function closeJsonSchemaEditorWithUpdate(
  eventBus: any,
  value: string,
  closeFn: () => void,
  beforeClose?: () => void
) {
  if (beforeClose) {
    beforeClose();
  }
  fireJsonSchemaUpdate(eventBus, value);
  closeFn();
}

/**
 * Helper to close message editor and optionally refresh message models
 */
export function closeMessageEditorAndRefresh(
  messageEvent: any,
  closeFn: () => void,
  onMessagesRequested?: (event: any) => void
) {
  closeFn();
  if (messageEvent && onMessagesRequested) {
    onMessagesRequested(messageEvent);
  }
}

/**
 * Helper to close script editor and persist the script update
 */
export function closeScriptEditorWithUpdate(
  eventBus: any,
  scriptType: string,
  script: string,
  element: any,
  closeFn: () => void,
  beforeClose?: () => void
) {
  if (beforeClose) {
    beforeClose();
  }
  fireScriptUpdate(eventBus, scriptType, script, element);
  closeFn();
}
