import { useCallback, useEffect, useState } from 'react';
import { ProcessGroup } from '../interfaces';
import HttpService from '../services/HttpService';
import { useUriListForPermissions } from './UriListForPermissions';

// cache will only help if user is clicking around a lot but we need to avoid issues
// where if a user updates a process group another user cannot see the update.
const CACHE_DURATION_MS = 60 * 1000;

const LOCAL_STORAGE_PROCESS_GROUP_CACHE_KEY = 'processGroupCache';

export default function useProcessGroupFetcher(processGroupIdentifier: string) {
  const [processGroup, setProcessGroup] = useState<ProcessGroup | null>(null);
  const { targetUris } = useUriListForPermissions();

  const getProcessGroupCache = useCallback(() => {
    return JSON.parse(
      localStorage.getItem(LOCAL_STORAGE_PROCESS_GROUP_CACHE_KEY) || '{}',
    );
  }, []);

  useEffect(() => {
    const storedProcessGroups = getProcessGroupCache();

    const handleProcessGroupResponse = (result: any) => {
      const timestamp = Date.now();
      const processGroups = result.results;
      processGroups.forEach((pg: ProcessGroup) => {
        storedProcessGroups[pg.id] = { processGroup: pg, timestamp };
        if (pg.id === processGroupIdentifier) {
          setProcessGroup(pg);
        }
      });
      localStorage.setItem(
        'storedProcessGroups',
        JSON.stringify(storedProcessGroups),
      );
    };

    const fetchProcessGroups = () => {
      const parentProcessGroupIdentifier = processGroupIdentifier
        .split('/')
        .slice(0, -1)
        .join('/');

      HttpService.makeCallToBackend({
        path: `${targetUris.processGroupListPath}?process_group_identifier=${parentProcessGroupIdentifier}&per_page=1000`,
        successCallback: handleProcessGroupResponse,
      });
    };

    if (processGroupIdentifier in storedProcessGroups) {
      const pg = storedProcessGroups[processGroupIdentifier].processGroup;
      const { timestamp } = storedProcessGroups[processGroupIdentifier];

      if (Date.now() - timestamp < CACHE_DURATION_MS) {
        setProcessGroup(pg);
      } else {
        fetchProcessGroups();
      }
    } else {
      fetchProcessGroups();
    }
  }, [
    processGroupIdentifier,
    targetUris.processGroupListPath,
    getProcessGroupCache,
  ]);

  const updateProcessGroupCache = (updatedProcessGroup: ProcessGroup) => {
    const storedProcessGroups = getProcessGroupCache();
    const timestamp = Date.now();

    storedProcessGroups[updatedProcessGroup.id] = {
      processGroup: updatedProcessGroup,
      timestamp,
    };
    localStorage.setItem(
      LOCAL_STORAGE_PROCESS_GROUP_CACHE_KEY,
      JSON.stringify(storedProcessGroups),
    );
  };

  return { processGroup, updateProcessGroupCache };
}
