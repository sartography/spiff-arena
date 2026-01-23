// Main component exports
export { default as BpmnEditor } from './components/BpmnEditor';
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
} from './hooks/useBpmnEditorLaunchers';
export type {
    UseBpmnEditorLaunchersOptions,
    BpmnEditorLaunchers,
    ScriptEditorState,
    MarkdownEditorState,
    MessageEditorState,
    JsonSchemaEditorState,
    ProcessSearchState as ProcessSearchLauncherState,
} from './hooks/useBpmnEditorLaunchers';

