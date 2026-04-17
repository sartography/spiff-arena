import { ReactElement } from 'react';
import { BpmnApiService } from '../services/BpmnApiService';

export interface ProcessReference {
  relative_location: string;
  display_name: string;
}

export interface BasicTask {
  id: number;
  guid?: string;
  process_instance_id?: number;
  bpmn_identifier: string;
  bpmn_name?: string;
  bpmn_process_direct_parent_guid?: string;
  bpmn_process_definition_identifier: string;
  typename: string;
  state: string;
  runtime_info?: Record<string, any>;
  properties_json?: Record<string, any>;
}

export interface ProcessModel {
  id: string;
  display_name: string;
  description?: string;
  primary_file_name?: string;
}

export interface BpmnEditorProps {
  /** Colon-separated process model identifier (URL-safe format, e.g., "group:subgroup:model") */
  modifiedProcessModelId: string;
  diagramType: 'bpmn' | 'dmn' | 'readonly';
  apiService: BpmnApiService;
  activeUserElement?: ReactElement;
  callers?: ProcessReference[];
  diagramXML?: string | null;
  disableSaveButton?: boolean;
  fileName?: string;
  isPrimaryFile?: boolean;
  processModel?: ProcessModel | null;
  tasks?: BasicTask[] | null;
  url?: string;

  // Event handlers
  onCallActivityOverlayClick?: (...args: any[]) => any;
  onDataStoresRequested?: (...args: any[]) => any;
  onDeleteFile?: (...args: any[]) => any;
  onDmnFilesRequested?: (...args: any[]) => any;
  onElementClick?: (...args: any[]) => any;
  onElementsChanged?: (...args: any[]) => any;
  onJsonSchemaFilesRequested?: (...args: any[]) => any;
  onLaunchBpmnEditor?: (...args: any[]) => any;
  onLaunchDmnEditor?: (...args: any[]) => any;
  onLaunchJsonSchemaEditor?: (...args: any[]) => any;
  onLaunchMarkdownEditor?: (...args: any[]) => any;
  onLaunchScriptEditor?: (...args: any[]) => any;
  onLaunchMessageEditor?: (...args: any[]) => any;
  onMessagesRequested?: (...args: any[]) => any;
  onSearchProcessModels?: (...args: any[]) => any;
  onServiceTasksRequested?: (...args: any[]) => any;
  onSetPrimaryFile?: (...args: any[]) => any;
  saveDiagram?: (...args: any[]) => any;
}

export interface DiagramModeler {
  importXML: (xml: string) => Promise<any>;
  saveXML: (options: { format: boolean }) => Promise<{ xml: string }>;
  get: (service: string) => any;
  on: (event: string, handler: (...args: any[]) => any) => void;
  destroy: () => void;
}

export interface BpmnViewerProps {
  /** Colon-separated process model identifier (URL-safe format, e.g., "group:subgroup:model") */
  modifiedProcessModelId: string;
  apiService: BpmnApiService;
  diagramXML?: string | null;
  fileName?: string;
  tasks?: BasicTask[] | null;
  url?: string;
  onElementClick?: (...args: any[]) => any;
  onCallActivityOverlayClick?: (...args: any[]) => any;
}

export type DiagramType = 'bpmn' | 'dmn' | 'readonly';

export interface ZoomControls {
  zoomIn: () => void;
  zoomOut: () => void;
  zoomFit: () => void;
}