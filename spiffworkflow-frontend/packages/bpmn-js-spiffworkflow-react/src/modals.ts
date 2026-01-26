// Modal components that require heavy UI dependencies
// Import these separately: import { ScriptEditorModal } from 'bpmn-js-spiffworkflow-react/modals'

// Modal components
export {
    ScriptEditorModal,
    MarkdownEditorModal,
    MessageEditorModal,
    JsonSchemaEditorModal,
    ProcessSearchModal,
} from './components/modals';
export type {
    ScriptEditorModalProps,
    MarkdownEditorModalProps,
    MessageEditorModalProps,
    JsonSchemaEditorModalProps,
    ProcessSearchModalProps,
} from './components/modals';

// Also export BpmnEditorWithModals since it uses modals
export { default as BpmnEditorWithModals } from './components/BpmnEditorWithModals';
export type {
    BpmnEditorWithModalsProps,
} from './components/BpmnEditorWithModals';
