import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { ProcessGroup } from '../../interfaces';
import HttpService from '../../services/HttpService';

/**
 * Grab Process Groups using HttpService from the Spiff API.
 * TODO: We'll need to allow appending the path to hit different endpoints.
 * Right now we're just grabbing them all
 */
export default function useProcessGroups({
  processInfo,
}: {
  processInfo: Record<string, any>;
}) {
  const [processGroups, setProcessGroups] = useState<ProcessGroup[] | null>(
    null,
  );
  // const [processModels, setProcessModels] = useState<ProcessModel[] | null>(
  //   null,
  // );
  const [loading, setLoading] = useState(false);

  // const handleProcessModelResponse = (result: any) => {
  //   setProcessModels(result.results);
  //   setLoading(false);
  // };
  const handleProcessGroupResponse = (result: any) => {
    setProcessGroups(result.results);
    setLoading(false);
    // HttpService.makeCallToBackend({
    //   path: '/process-models?per_page=1000&recursive=true&filter_runnable_by_user=true',
    //   httpMethod: 'GET',
    //   successCallback: handleProcessModelResponse,
    // });
  };

  const path = '/process-groups?filter_runnable_by_user=true';
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
    // processModels,
    loading,
  };
}
