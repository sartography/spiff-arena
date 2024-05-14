import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import HttpService from '../../services/HttpService';

/**
 * Grab tasks using HttpService from the Spiff API.
 * TODO: We'll need to allow appending the path to hit different endpoints.
 * Right now we're just grabbing for-me
 */
export default function useTaskCollection({
  processInfo,
}: {
  processInfo: Record<string, any>;
}) {
  const [taskCollection, setTaskCollection] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(false);

  /**
   * Query function to get tasks from the backend
   * @returns Query functions must return a value, even if it's just true
   */
  const processResult = (result: any[]) => {
    setTaskCollection(result);
    setLoading(false);
  };

  const path = '/tasks';
  const getTaskCollection = async () => {
    setLoading(true);
    // TODO: Currently, the API endpoint for this is an SSE endpoint, so we can't use the HttpService.
    // We'll need to refactor this to use the SSE service, or change the API to return a RESTful response.
    // const path = processInfo?.id ? `/tasks/${processInfo.id}` : '/tasks';
    HttpService.makeCallToBackend({
      path,
      httpMethod: 'GET',
      successCallback: processResult,
    });

    return true;
  };

  /** TanStack (React Query) trigger to do it's SWR state/cache thing */
  useQuery({
    queryKey: [path, processInfo],
    queryFn: () => getTaskCollection(),
  });

  return {
    taskCollection,
    loading,
  };
}
