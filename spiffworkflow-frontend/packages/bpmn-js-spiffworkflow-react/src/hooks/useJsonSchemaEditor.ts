import { useState, useEffect, useCallback } from 'react';
import {
  extractSchemaBaseName,
  toValidSchemaName,
  validateSchemaName,
  getSchemaFileNames,
  deriveSchemaNameFromElement,
} from '../utils/schemaHelpers';
import { BpmnApiService } from '../services/BpmnApiService';

export interface JsonSchemaEditorState {
  /** Current mode: 'create' for new schema, 'edit' for existing */
  mode: 'create' | 'edit';
  /** Whether files are being loaded */
  loading: boolean;
  /** Whether files are being saved */
  saving: boolean;
  /** Error message if any */
  error: string | null;
  /** Base name of the schema (without extension) */
  baseName: string;
  /** Name input for create mode */
  newSchemaName: string;
  /** Validation error for name input */
  nameError: string | null;
  /** Schema file content */
  schemaContent: string;
  /** UI Schema file content */
  uiSchemaContent: string;
  /** Example data file content */
  exampleDataContent: string;
  /** Whether there are unsaved changes */
  hasChanges: boolean;
  /** Derived file names */
  fileNames: {
    schemaFile: string;
    uiSchemaFile: string;
    exampleDataFile: string;
  };
}

export interface JsonSchemaEditorActions {
  /** Set the new schema name (for create mode) */
  setNewSchemaName: (name: string) => void;
  /** Update schema content */
  setSchemaContent: (content: string) => void;
  /** Update UI schema content */
  setUiSchemaContent: (content: string) => void;
  /** Update example data content */
  setExampleDataContent: (content: string) => void;
  /** Create the schema files (for create mode) */
  createSchema: () => Promise<boolean>;
  /** Save all schema files */
  save: () => Promise<boolean>;
  /** Close and fire update event */
  close: () => void;
  /** Validate JSON content */
  validateJson: (content: string) => boolean;
  /** Reset state for next use */
  reset: () => void;
}

export interface UseJsonSchemaEditorOptions {
  /** Whether the editor is open */
  open: boolean;
  /** Initial file name (empty for new schema) */
  fileName: string;
  /** Colon-separated process model identifier (URL-safe format, e.g., "group:subgroup:model") */
  modifiedProcessModelId: string;
  /** API service for file operations */
  apiService: BpmnApiService;
  /** Event bus for firing updates */
  eventBus?: any;
  /** BPMN element for deriving default name */
  element?: any;
  /** Callback when editor closes */
  onClose?: () => void;
  /** Callback on successful save */
  onSave?: () => void;
  /** Callback on error */
  onError?: (error: string) => void;
}

/**
 * Headless hook for JSON Schema editor logic
 * Handles all the business logic for creating/editing JSON schema files
 * Apps provide their own UI components
 */
export function useJsonSchemaEditor(
  options: UseJsonSchemaEditorOptions,
): [JsonSchemaEditorState, JsonSchemaEditorActions] {
  const {
    open,
    fileName,
    modifiedProcessModelId,
    apiService,
    eventBus,
    element,
    onClose,
    onSave,
    onError,
  } = options;

  // State
  const [mode, setMode] = useState<'create' | 'edit'>('edit');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [baseName, setBaseName] = useState('');
  const [newSchemaName, setNewSchemaName] = useState('');
  const [nameError, setNameError] = useState<string | null>(null);
  const [schemaContent, setSchemaContent] = useState('{}');
  const [uiSchemaContent, setUiSchemaContent] = useState('{}');
  const [exampleDataContent, setExampleDataContent] = useState('{}');
  const [hasChanges, setHasChanges] = useState(false);

  // Derived file names
  const fileNames = baseName
    ? getSchemaFileNames(baseName)
    : {
        schemaFile: '',
        uiSchemaFile: '',
        exampleDataFile: '',
      };

  // Initialize mode and baseName when editor opens
  useEffect(() => {
    if (!open) return;

    const existingBaseName = extractSchemaBaseName(fileName);

    if (existingBaseName) {
      setMode('edit');
      setBaseName(existingBaseName);
      setNewSchemaName('');
    } else {
      setMode('create');
      setBaseName('');
      const defaultName = deriveSchemaNameFromElement(element);
      setNewSchemaName(defaultName);
      setLoading(false);
    }
  }, [open, fileName, element]);

  // Load files when in edit mode
  useEffect(() => {
    if (!open || !modifiedProcessModelId || mode !== 'edit' || !baseName)
      return;

    const loadFiles = async () => {
      setLoading(true);
      setError(null);

      const names = getSchemaFileNames(baseName);

      try {
        // Load schema file
        try {
          const response = await apiService.loadDiagramFile(
            modifiedProcessModelId,
            names.schemaFile,
          );
          setSchemaContent(
            typeof response.file_contents === 'string'
              ? response.file_contents
              : JSON.stringify(response.file_contents, null, 2),
          );
        } catch {
          setSchemaContent('{}');
        }

        // Load UI schema file
        try {
          const response = await apiService.loadDiagramFile(
            modifiedProcessModelId,
            names.uiSchemaFile,
          );
          setUiSchemaContent(
            typeof response.file_contents === 'string'
              ? response.file_contents
              : JSON.stringify(response.file_contents, null, 2),
          );
        } catch {
          setUiSchemaContent('{}');
        }

        // Load example data file
        try {
          const response = await apiService.loadDiagramFile(
            modifiedProcessModelId,
            names.exampleDataFile,
          );
          setExampleDataContent(
            typeof response.file_contents === 'string'
              ? response.file_contents
              : JSON.stringify(response.file_contents, null, 2),
          );
        } catch {
          setExampleDataContent('{}');
        }
      } catch (err) {
        console.error('Error loading JSON schema files:', err);
        setError('Failed to load schema files');
        onError?.('Failed to load schema files');
      } finally {
        setLoading(false);
      }
    };

    loadFiles();
  }, [open, modifiedProcessModelId, apiService, mode, baseName, onError]);

  // Validate JSON
  const validateJson = useCallback((content: string): boolean => {
    try {
      JSON.parse(content);
      return true;
    } catch {
      return false;
    }
  }, []);

  // Handle name change for create mode
  const handleSetNewSchemaName = useCallback((value: string) => {
    const sanitized = toValidSchemaName(value);
    setNewSchemaName(sanitized);
    setNameError(null);
  }, []);

  // Handle content changes
  const handleSetSchemaContent = useCallback((content: string) => {
    setSchemaContent(content);
    setHasChanges(true);
  }, []);

  const handleSetUiSchemaContent = useCallback((content: string) => {
    setUiSchemaContent(content);
    setHasChanges(true);
  }, []);

  const handleSetExampleDataContent = useCallback((content: string) => {
    setExampleDataContent(content);
    setHasChanges(true);
  }, []);

  // Create schema files
  const createSchema = useCallback(async (): Promise<boolean> => {
    const validationError = validateSchemaName(newSchemaName);
    if (validationError) {
      setNameError(validationError);
      return false;
    }

    setSaving(true);
    try {
      const names = getSchemaFileNames(newSchemaName);
      await apiService.saveDiagramFile(
        modifiedProcessModelId,
        names.schemaFile,
        '{}',
      );
      await apiService.saveDiagramFile(
        modifiedProcessModelId,
        names.uiSchemaFile,
        '{}',
      );
      await apiService.saveDiagramFile(
        modifiedProcessModelId,
        names.exampleDataFile,
        '{}',
      );

      setBaseName(newSchemaName);
      setMode('edit');
      setSchemaContent('{}');
      setUiSchemaContent('{}');
      setExampleDataContent('{}');
      setLoading(false);

      onSave?.();
      return true;
    } catch (err) {
      console.error('Error creating schema files:', err);
      onError?.('Failed to create schema files');
      return false;
    } finally {
      setSaving(false);
    }
  }, [newSchemaName, apiService, modifiedProcessModelId, onSave, onError]);

  // Save all files
  const save = useCallback(async (): Promise<boolean> => {
    if (!baseName) {
      onError?.('No schema name set');
      return false;
    }

    if (!validateJson(schemaContent)) {
      onError?.('Invalid JSON in Schema');
      return false;
    }
    if (!validateJson(uiSchemaContent)) {
      onError?.('Invalid JSON in UI Schema');
      return false;
    }
    if (!validateJson(exampleDataContent)) {
      onError?.('Invalid JSON in Example Data');
      return false;
    }

    setSaving(true);
    try {
      await apiService.saveDiagramFile(
        modifiedProcessModelId,
        fileNames.schemaFile,
        schemaContent,
      );
      await apiService.saveDiagramFile(
        modifiedProcessModelId,
        fileNames.uiSchemaFile,
        uiSchemaContent,
      );
      await apiService.saveDiagramFile(
        modifiedProcessModelId,
        fileNames.exampleDataFile,
        exampleDataContent,
      );

      setHasChanges(false);
      onSave?.();
      return true;
    } catch (err) {
      console.error('Error saving schema files:', err);
      onError?.('Failed to save schema files');
      return false;
    } finally {
      setSaving(false);
    }
  }, [
    baseName,
    schemaContent,
    uiSchemaContent,
    exampleDataContent,
    fileNames,
    apiService,
    modifiedProcessModelId,
    validateJson,
    onSave,
    onError,
  ]);

  // Close and fire update
  const close = useCallback(() => {
    if (eventBus && baseName) {
      eventBus.fire('spiff.jsonSchema.update', {
        value: `${baseName}-schema.json`,
      });
    }
    onClose?.();
  }, [eventBus, baseName, onClose]);

  // Reset state
  const reset = useCallback(() => {
    setMode('edit');
    setBaseName('');
    setNewSchemaName('');
    setNameError(null);
    setSchemaContent('{}');
    setUiSchemaContent('{}');
    setExampleDataContent('{}');
    setHasChanges(false);
    setError(null);
  }, []);

  const state: JsonSchemaEditorState = {
    mode,
    loading,
    saving,
    error,
    baseName,
    newSchemaName,
    nameError,
    schemaContent,
    uiSchemaContent,
    exampleDataContent,
    hasChanges,
    fileNames,
  };

  const actions: JsonSchemaEditorActions = {
    setNewSchemaName: handleSetNewSchemaName,
    setSchemaContent: handleSetSchemaContent,
    setUiSchemaContent: handleSetUiSchemaContent,
    setExampleDataContent: handleSetExampleDataContent,
    createSchema,
    save,
    close,
    validateJson,
    reset,
  };

  return [state, actions];
}
