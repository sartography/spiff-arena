import { useCallback, useEffect, useState } from 'react';
import { BpmnApiService } from '../services/BpmnApiService';

export interface ProcessReference {
  identifier: string;
  display_name: string;
  relative_location: string;
  type: string;
  file_name: string;
  properties: any;
}

export interface UseProcessReferencesOptions {
  apiService: BpmnApiService;
}

export interface ProcessReferencesState {
  processes: ProcessReference[];
  loading: boolean;
  error: string | null;
}

export interface ProcessReferencesActions {
  refresh: () => Promise<ProcessReference[]>;
}

export function useProcessReferences(
  options: UseProcessReferencesOptions
): [ProcessReferencesState, ProcessReferencesActions] {
  const { apiService } = options;
  const [processes, setProcesses] = useState<ProcessReference[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const normalizeProcess = useCallback((item: any): ProcessReference => {
    return {
      identifier: item.identifier || item.primary_process_id || item.id || '',
      display_name: item.display_name || item.name || '',
      relative_location: item.relative_location || item.location || item.id || '',
      type: item.type || 'process',
      file_name: item.file_name || item.primary_file_name || '',
      properties: item.properties || {},
    };
  }, []);

  const loadProcesses = useCallback(async (): Promise<ProcessReference[]> => {
    setLoading(true);
    setError(null);

    try {
      if (apiService.getProcesses) {
        const results = await apiService.getProcesses();
        const normalized = (results || []).map(normalizeProcess);
        setProcesses(normalized);
        return normalized;
      }

      if (apiService.searchProcessModels) {
        const results = await apiService.searchProcessModels('');
        const mapped = results?.map(normalizeProcess) || [];
        setProcesses(mapped);
        return mapped;
      }

      setProcesses([]);
      return [];
    } catch (err) {
      console.error('Error loading processes:', err);
      setError('Failed to load processes');
      return [];
    } finally {
      setLoading(false);
    }
  }, [apiService, normalizeProcess]);

  useEffect(() => {
    loadProcesses();
  }, [loadProcesses]);

  return [
    {
      processes,
      loading,
      error,
    },
    {
      refresh: loadProcesses,
    },
  ];
}
