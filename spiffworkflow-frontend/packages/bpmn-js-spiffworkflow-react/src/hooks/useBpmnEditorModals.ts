import { useCallback, useState } from 'react';
import {
  MarkdownEditorState,
  MessageEditorState,
  JsonSchemaEditorState,
  ProcessSearchState,
  ScriptEditorState,
  fireCallActivityUpdate,
  useBpmnEditorLaunchers,
} from './useBpmnEditorLaunchers';

export function useBpmnEditorModals() {
  const [scriptEditorState, setScriptEditorState] =
    useState<ScriptEditorState | null>(null);
  const [markdownEditorState, setMarkdownEditorState] =
    useState<MarkdownEditorState | null>(null);
  const [messageEditorState, setMessageEditorState] =
    useState<MessageEditorState | null>(null);
  const [jsonSchemaEditorState, setJsonSchemaEditorState] =
    useState<JsonSchemaEditorState | null>(null);
  const [processSearchState, setProcessSearchState] =
    useState<ProcessSearchState | null>(null);

  const launchers = useBpmnEditorLaunchers({
    onOpenScriptEditor: setScriptEditorState,
    onOpenMarkdownEditor: setMarkdownEditorState,
    onOpenMessageEditor: setMessageEditorState,
    onOpenJsonSchemaEditor: setJsonSchemaEditorState,
    onOpenProcessSearch: setProcessSearchState,
  });

  const closeScriptEditor = useCallback(() => setScriptEditorState(null), []);
  const closeMarkdownEditor = useCallback(
    () => setMarkdownEditorState(null),
    [],
  );
  const closeMessageEditor = useCallback(() => setMessageEditorState(null), []);
  const closeJsonSchemaEditor = useCallback(
    () => setJsonSchemaEditorState(null),
    [],
  );
  const closeProcessSearch = useCallback(
    () => setProcessSearchState(null),
    [],
  );
  const selectProcessSearchResult = useCallback(
    (processId?: string) => {
      if (
        processId &&
        processSearchState?.eventBus &&
        processSearchState?.element
      ) {
        fireCallActivityUpdate(
          processSearchState.eventBus,
          processSearchState.element,
          processId,
        );
      }
      setProcessSearchState(null);
    },
    [processSearchState],
  );

  return {
    ...launchers,
    scriptEditorState,
    markdownEditorState,
    messageEditorState,
    jsonSchemaEditorState,
    processSearchState,
    closeScriptEditor,
    closeMarkdownEditor,
    closeMessageEditor,
    closeJsonSchemaEditor,
    closeProcessSearch,
    selectProcessSearchResult,
  };
}
