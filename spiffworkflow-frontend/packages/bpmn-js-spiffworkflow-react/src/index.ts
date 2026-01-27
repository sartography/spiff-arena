// Main component exports
export { default as BpmnEditor } from './components/BpmnEditor';
export { default as ProcessSearch } from './components/ProcessSearch';
export { default as MessageEditorDialog } from './components/MessageEditorDialog';
export { default as MessageEditor } from './components/messages/MessageEditor';
export { default as MarkdownEditorDialog } from './components/MarkdownEditorDialog';
export { default as JsonSchemaEditorDialog } from './components/JsonSchemaEditorDialog';
export { default as DialogShell } from './components/DialogShell';
export { default as FileNameEditorDialog } from './components/FileNameEditorDialog';
export { default as ScriptAssistPanel } from './components/ScriptAssistPanel';
export { default as ScriptEditorDialog } from './components/ScriptEditorDialog';
export { default as ProcessSearchDialog } from './components/ProcessSearchDialog';
export { default as DiagramActionBar } from './components/DiagramActionBar';
export { default as DiagramZoomControls } from './components/DiagramZoomControls';
export { default as ProcessReferencesDialog } from './components/ProcessReferencesDialog';
export { default as DiagramNavigationBreadcrumbs } from './components/DiagramNavigationBreadcrumbs';
export type {
    BpmnEditorRef,
    BpmnEditorInternalProps,
} from './components/BpmnEditor';

// Type exports
export type {
    BpmnEditorProps,
    BpmnViewerProps,
    BasicTask,
    ProcessModel,
    ProcessReference,
    DiagramModeler,
    DiagramType,
    ZoomControls,
} from './types';

// Service exports
export {
    DefaultBpmnApiService,
    SpiffWorkflowApiService,
} from './services/BpmnApiService';
export type { BpmnApiService, BpmnApiConfig } from './services/BpmnApiService';

// Utility exports
export {
    getBpmnProcessIdentifiers,
    convertSvgElementToHtmlString,
    makeid,
    taskIsMultiInstanceChild,
    checkTaskCanBeHighlighted,
} from './utils/bpmnHelpers';

// Schema utility exports
export {
    SCHEMA_NAME_PATTERN,
    SCHEMA_EXTENSIONS,
    extractSchemaBaseName,
    toValidSchemaName,
    validateSchemaName,
    getSchemaFileNames,
    isSchemaFile,
    deriveSchemaNameFromElement,
} from './utils/schemaHelpers';

// Headless hook exports
export { useJsonSchemaEditor } from './hooks/useJsonSchemaEditor';
export type {
    JsonSchemaEditorState,
    JsonSchemaEditorActions,
    UseJsonSchemaEditorOptions,
} from './hooks/useJsonSchemaEditor';

export {
    useProcessSearch,
    formatProcessLabel,
    getProcessValue,
} from './hooks/useProcessSearch';
export type {
    ProcessSearchResult,
    ProcessSearchState,
    ProcessSearchActions,
    UseProcessSearchOptions,
} from './hooks/useProcessSearch';
export { useProcessReferences } from './hooks/useProcessReferences';
export type {
    ProcessReference as ProcessReferenceResult,
    ProcessReferencesState,
    ProcessReferencesActions,
    UseProcessReferencesOptions,
} from './hooks/useProcessReferences';

export {
    useBpmnEditorCallbacks,
    findFileNameForReferenceId,
} from './hooks/useBpmnEditorCallbacks';
export type {
    UseBpmnEditorCallbacksOptions,
    BpmnEditorCallbacks,
    ProcessFile,
} from './hooks/useBpmnEditorCallbacks';

export {
    useBpmnEditorLaunchers,
    fireScriptUpdate,
    fireMarkdownUpdate,
    fireJsonSchemaUpdate,
    fireMessageSave,
    fireCallActivityUpdate,
    closeMarkdownEditorWithUpdate,
    closeJsonSchemaEditorWithUpdate,
    closeMessageEditorAndRefresh,
    closeScriptEditorWithUpdate,
} from './hooks/useBpmnEditorLaunchers';
export { useBpmnEditorModals } from './hooks/useBpmnEditorModals';
export { useBpmnEditorTextEditorsState } from './hooks/useBpmnEditorTextEditorsState';
export { useBpmnEditorScriptState } from './hooks/useBpmnEditorScriptState';
export { useScriptUnitTestsState } from './hooks/useScriptUnitTestsState';
export { runScriptUnitTest } from './hooks/useScriptUnitTestRunner';
export { useDiagramNavigationStack } from './hooks/useDiagramNavigationStack';
export { useDiagramNavigationHandlers } from './hooks/useDiagramNavigationHandlers';
export type {
    UseBpmnEditorLaunchersOptions,
    BpmnEditorLaunchers,
    ScriptEditorState,
    MarkdownEditorState,
    MessageEditorState,
    ProcessSearchState as ProcessSearchLauncherState,
} from './hooks/useBpmnEditorLaunchers';
export type {
    UseBpmnEditorTextEditorsStateOptions,
    BpmnEditorTextEditorsState,
} from './hooks/useBpmnEditorTextEditorsState';
export type { DiagramNavigationItem } from './hooks/useDiagramNavigationStack';
export type {
    UseBpmnEditorScriptStateOptions,
    BpmnEditorScriptState,
} from './hooks/useBpmnEditorScriptState';
export type {
    UseScriptUnitTestsStateOptions,
    ScriptUnitTestState,
    ScriptUnitTestActions,
} from './hooks/useScriptUnitTestsState';
export type {
    RunScriptUnitTestOptions,
    ScriptUnitTestRunPayload,
} from './hooks/useScriptUnitTestRunner';
