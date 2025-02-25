import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { ProcessGroup, ProcessGroupLite } from '../interfaces';
import HttpService from '../services/HttpService';

/**
 * Grab Process Groups using HttpService from the Spiff API.
 * TODO: We'll need to allow appending the path to hit different endpoints.
 * Right now we're just grabbing them all
 */
export default function useProcessGroups({
  processInfo,
  getRunnableProcessModels = false,
}: {
  processInfo: Record<string, any>;
  getRunnableProcessModels?: boolean;
}) {
  const [processGroups, setProcessGroups] = useState<
    ProcessGroup[] | ProcessGroupLite[] | null
  >(null);
  const [loading, setLoading] = useState(false);

  const handleProcessGroupResponse = (result: any) => {
    setProcessGroups(result.results);
    setLoading(false);
  };

  let path = '/process-groups';
  if (getRunnableProcessModels) {
    path =
      '/process-models?filter_runnable_by_user=true&recursive=true&group_by_process_group=True&per_page=2000';
  }
  const getProcessGroups = async () => {
    setLoading(true);
    HttpService.makeCallToBackend({
      path,
      httpMethod: 'GET',
      successCallback: handleProcessGroupResponse,
    });

    // return required for Tanstack query
    return true;
  };

  useQuery({
    queryKey: [path, processInfo],
    queryFn: () => getProcessGroups(),
  });

  return {
    processGroups,
    loading,
  };
}
