import { useEffect, useState } from 'react';
import { ProcessGroup } from '../interfaces';
import HttpService from '../services/HttpService';
import { useUriListForPermissions } from './UriListForPermissions';

export default function useProcessGroupFetcher(processGroupIdentifier: string) {
  const [processGroup, setProcessGroup] = useState<ProcessGroup | null>(null);
  const { targetUris } = useUriListForPermissions();

  useEffect(() => {
    const storedProcessGroups = JSON.parse(
      localStorage.getItem('storedProcessGroups') || '{}'
    );
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
        JSON.stringify(storedProcessGroups)
      );
    };

    const fetchProcessGroups = () => {
      const parentProcessGroupIdentifier = processGroupIdentifier
        .split('/')
        .slice(0, -1)
        .join('/');

      HttpService.makeCallToBackend({
        path: `${targetUris.processGroupListPath}?process_group_identifier=${parentProcessGroupIdentifier}`,
        successCallback: handleProcessGroupResponse,
      });
    };
    if (processGroupIdentifier in storedProcessGroups) {
      const pg = storedProcessGroups[processGroupIdentifier].processGroup;
      const { timestamp } = storedProcessGroups[processGroupIdentifier];

      // cache will only help if user is clicking around a lot but we need to avoid issues
      // where if a user updates a process group another user cannot see the update.
      const cacheDuration = 60 * 1000;

      if (Date.now() - timestamp < cacheDuration) {
        setProcessGroup(pg);
      } else {
        fetchProcessGroups();
      }
    } else {
      fetchProcessGroups();
    }
  }, [processGroupIdentifier, targetUris.processGroupListPath]);

  return processGroup;
}
