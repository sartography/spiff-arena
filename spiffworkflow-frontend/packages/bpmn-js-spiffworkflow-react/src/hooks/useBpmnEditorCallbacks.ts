import { useCallback } from 'react';
import { BpmnApiService } from '../services/BpmnApiService';

export interface ProcessModel {
  id: string;
  display_name: string;
  description?: string;
  primary_file_name?: string;
  parent_groups?: Array<{ id: string }>;
  files?: Array<{
    name: string;
    type: string;
    references: Array<{
      identifier: string;
      display_name: string;
    }>;
  }>;
}

export interface ProcessFile {
  name: string;
  type: string;
  file_contents_hash?: string;
  references: Array<{
    identifier: string;
    display_name: string;
    file_name: string;
  }>;
}

export interface UseBpmnEditorCallbacksOptions {
  /** API service for making backend calls */
  apiService: BpmnApiService;
  /** Current process model */
  processModel?: ProcessModel | null;
  /** Whether user can access messages endpoint */
  canAccessMessages?: boolean;
  /** Message model list API path */
  messageModelListPath?: string;
}

export interface BpmnEditorCallbacks {
  /** Handle service tasks requested event */
  onServiceTasksRequested: (event: any) => void;
  /** Handle data stores requested event */
  onDataStoresRequested: (event: any) => void;
  /** Handle JSON schema files requested event */
  onJsonSchemaFilesRequested: (event: any) => void;
  /** Handle DMN files requested event */
  onDmnFilesRequested: (event: any) => void;
  /** Handle messages requested event */
  onMessagesRequested: (event: any) => void;
}

/**
 * Hook that provides reusable callback implementations for BPMN editor events.
 * These callbacks handle API requests and fire events back to bpmn-js.
 *
 * @example
 * ```tsx
 * const callbacks = useBpmnEditorCallbacks({
 *   apiService: myApiService,
 *   processModel,
 *   canAccessMessages: true,
 *   messageModelListPath: '/messages'
 * });
 *
 * <BpmnEditor
 *   {...callbacks}
 *   onLaunchScriptEditor={myScriptEditorHandler}
 * />
 * ```
 */
export function useBpmnEditorCallbacks(
  options: UseBpmnEditorCallbacksOptions
): BpmnEditorCallbacks {
  const { apiService, processModel, canAccessMessages, messageModelListPath } = options;

  /**
   * Handle service tasks requested event
   * Fetches available service task operators from the backend
   */
  const onServiceTasksRequested = useCallback(
    (event: any) => {
      if (!apiService.getServiceTasks) {
        console.warn('apiService.getServiceTasks not implemented');
        return;
      }

      apiService
        .getServiceTasks()
        .then((results) => {
          event.eventBus.fire('spiff.service_tasks.returned', {
            serviceTaskOperators: results,
          });
        })
        .catch((error) => {
          console.error('Error fetching service tasks:', error);
        });
    },
    [apiService]
  );

  /**
   * Handle data stores requested event
   * Fetches available data stores for the process model
   */
  const onDataStoresRequested = useCallback(
    (event: any) => {
      if (!apiService.getDataStores) {
        console.warn('apiService.getDataStores not implemented');
        return;
      }

      const processGroupIdentifier =
        processModel?.parent_groups?.slice(-1).pop()?.id ?? '';

      apiService
        .getDataStores(processGroupIdentifier)
        .then((results) => {
          event.eventBus.fire('spiff.data_stores.returned', {
            options: results,
          });
        })
        .catch((error) => {
          console.error('Error fetching data stores:', error);
        });
    },
    [apiService, processModel?.parent_groups]
  );

  /**
   * Handle JSON schema files requested event
   * Returns list of *-schema.json files from the process model
   */
  const onJsonSchemaFilesRequested = useCallback(
    (event: any) => {
      const re = /.*[-.]schema.json/;
      if (processModel?.files) {
        const jsonFiles = processModel.files.filter((f) => f.name.match(re));
        const options = jsonFiles.map((f) => {
          return { label: f.name, value: f.name };
        });
        event.eventBus.fire('spiff.json_schema_files.returned', { options });
      } else {
        console.warn('Process model or files not available for JSON schema request');
      }
    },
    [processModel?.files]
  );

  /**
   * Handle DMN files requested event
   * Returns list of DMN decision references from the process model
   */
  const onDmnFilesRequested = useCallback(
    (event: any) => {
      if (processModel?.files) {
        const dmnFiles = processModel.files.filter((f) => f.type === 'dmn');
        const options: any[] = [];
        dmnFiles.forEach((file) => {
          file.references.forEach((ref) => {
            options.push({ label: ref.display_name, value: ref.identifier });
          });
        });
        event.eventBus.fire('spiff.dmn_files.returned', { options });
      } else {
        console.warn('Process model or files not available for DMN request');
      }
    },
    [processModel?.files]
  );

  /**
   * Handle messages requested event
   * Fetches available message models from the backend
   */
  const onMessagesRequested = useCallback(
    (event: any) => {
      if (!canAccessMessages) {
        console.warn('Message access not configured');
        return;
      }

      if (!apiService.getMessages) {
        console.warn('apiService.getMessages not implemented');
        return;
      }

      apiService
        .getMessages(messageModelListPath)
        .then((results) => {
          event.eventBus.fire('spiff.messages.returned', {
            configuration: results,
          });
        })
        .catch((error) => {
          console.error('Error fetching messages:', error);
        });
    },
    [apiService, canAccessMessages, messageModelListPath]
  );

  return {
    onServiceTasksRequested,
    onDataStoresRequested,
    onJsonSchemaFilesRequested,
    onDmnFilesRequested,
    onMessagesRequested,
  };
}

/**
 * Helper function to find a file by reference ID and type
 * Used for navigating to DMN/BPMN files from the editor
 */
export function findFileNameForReferenceId(
  processModel: ProcessModel | null | undefined,
  id: string,
  type: string
): ProcessFile | null {
  if (!processModel?.files) {
    return null;
  }

  const files = processModel.files.filter((f) => f.type === type);
  let matchFile = null;

  files.some((file) => {
    if (file.references.some((ref) => ref.identifier === id)) {
      matchFile = file;
      return true;
    }
    return false;
  });

  return matchFile as ProcessFile | null;
}
