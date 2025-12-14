// Main component exports
export { default as BpmnEditor } from './components/BpmnEditor';
export type { BpmnEditorRef, BpmnEditorInternalProps } from './components/BpmnEditor';

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
export type {
  BpmnApiService,
  BpmnApiConfig,
} from './services/BpmnApiService';

// Utility exports
export {
  getBpmnProcessIdentifiers,
  convertSvgElementToHtmlString,
  makeid,
  taskIsMultiInstanceChild,
  checkTaskCanBeHighlighted,
} from './utils/bpmnHelpers';

// Re-export CSS for consumers who want to import styles
import './styles/bpmn-js-properties-panel.css';