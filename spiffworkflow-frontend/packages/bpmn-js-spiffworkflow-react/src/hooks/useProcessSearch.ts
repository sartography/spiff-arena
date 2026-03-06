import { useState, useEffect, useCallback } from 'react';
import { BpmnApiService } from '../services/BpmnApiService';

export interface ProcessSearchResult {
  id: string;
  display_name: string;
  primary_process_id: string;
  primary_file_name?: string;
  description?: string;
}

export interface ProcessSearchState {
  /** Whether the search modal is open */
  isOpen: boolean;
  /** Available processes for selection */
  processes: ProcessSearchResult[];
  /** Whether processes are being loaded */
  loading: boolean;
  /** Current search/filter query */
  query: string;
  /** Filtered processes based on query */
  filteredProcesses: ProcessSearchResult[];
  /** Error message if any */
  error: string | null;
}

export interface ProcessSearchActions {
  /** Open the search modal */
  open: (eventBus: any, element: any) => void;
  /** Close the search modal */
  close: () => void;
  /** Set the search query */
  setQuery: (query: string) => void;
  /** Select a process */
  select: (process: ProcessSearchResult | null) => void;
  /** Refresh the process list */
  refresh: () => Promise<void>;
}

export interface UseProcessSearchOptions {
  /** API service for fetching processes */
  apiService: BpmnApiService;
  /** Callback when a process is selected */
  onSelect?: (process: ProcessSearchResult) => void;
  /** Callback when modal closes */
  onClose?: () => void;
  /** Callback on error */
  onError?: (error: string) => void;
}

/**
 * Headless hook for process search/selection logic
 * Used for Call Activity process selection
 * Apps provide their own UI components (modal, autocomplete, etc.)
 */
export function useProcessSearch(
  options: UseProcessSearchOptions
): [ProcessSearchState, ProcessSearchActions] {
  const { apiService, onSelect, onClose, onError } = options;

  // State
  const [isOpen, setIsOpen] = useState(false);
  const [processes, setProcesses] = useState<ProcessSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState('');
  const [error, setError] = useState<string | null>(null);

  // Store event bus and element for firing updates
  const [eventBus, setEventBus] = useState<any>(null);
  const [element, setElement] = useState<any>(null);

  // Filter processes based on query
  const filteredProcesses = query
    ? processes.filter(
        (p) =>
          p.display_name.toLowerCase().includes(query.toLowerCase()) ||
          p.primary_process_id.toLowerCase().includes(query.toLowerCase()) ||
          p.id.toLowerCase().includes(query.toLowerCase())
      )
    : processes;

  // Load processes on mount and when apiService changes
  const loadProcesses = useCallback(async () => {
    if (!apiService.searchProcessModels) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const results = await apiService.searchProcessModels('');
      setProcesses(results || []);
    } catch (err) {
      console.error('Error loading processes:', err);
      setError('Failed to load processes');
      onError?.('Failed to load processes');
    } finally {
      setLoading(false);
    }
  }, [apiService, onError]);

  // Load processes when hook is first used
  useEffect(() => {
    loadProcesses();
  }, [loadProcesses]);

  // Open the search modal
  const open = useCallback((bus: any, elem: any) => {
    setEventBus(bus);
    setElement(elem);
    setQuery('');
    setIsOpen(true);
  }, []);

  // Close the search modal
  const close = useCallback(() => {
    setIsOpen(false);
    setQuery('');
    onClose?.();
  }, [onClose]);

  // Handle selection
  const select = useCallback(
    (process: ProcessSearchResult | null) => {
      if (process && eventBus) {
        // Fire the update event to bpmn-js-spiffworkflow
        eventBus.fire('spiff.callactivity.update', {
          element,
          value: process.primary_process_id,
        });
        onSelect?.(process);
      }
      close();
    },
    [eventBus, element, onSelect, close]
  );

  // Set query with optional filtering
  const handleSetQuery = useCallback((newQuery: string) => {
    setQuery(newQuery);
  }, []);

  const state: ProcessSearchState = {
    isOpen,
    processes,
    loading,
    query,
    filteredProcesses,
    error,
  };

  const actions: ProcessSearchActions = {
    open,
    close,
    setQuery: handleSetQuery,
    select,
    refresh: loadProcesses,
  };

  return [state, actions];
}

/**
 * Format a process for display in a dropdown/autocomplete
 */
export function formatProcessLabel(process: ProcessSearchResult): string {
  return `${process.display_name} (${process.primary_process_id})`;
}

/**
 * Get the value to use when a process is selected
 */
export function getProcessValue(process: ProcessSearchResult): string {
  return process.primary_process_id;
}
