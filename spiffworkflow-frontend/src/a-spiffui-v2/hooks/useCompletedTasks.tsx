import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import HttpService from '../../services/HttpService';

/**
 * Grab Completed tasks using HttpService from the Spiff API.
 * TODO: This is a copy of useTaskCollection.tsx,
 * but it will probably be refactored to work differently.
 */
export default function useCompletedTasks({
  processInfo,
}: {
  processInfo: Record<string, any>;
}) {
  const [completedTasks, setCompletedTasks] = useState<Record<string, any>[]>(
    []
  );

  const [loading, setLoading] = useState(false);

  /**
   * Query function to get tasks from the backend
   * @returns Query functions must return a value, even if it's just true
   */
  const processResult = (result: Record<string, any>) => {
    setCompletedTasks(result.results);
    setLoading(false);
  };

  const apiCall = `/tasks/completed/${processInfo.id}`;
  const getTaskCollection = async () => {
    setLoading(true);
    // TODO: Currently, the API endpoint for this is an SSE endpoint, so we can't use the HttpService.
    // We'll need to refactor this to use the SSE service, or change the API to return a RESTful response.
    // const path = processInfo?.id ? `/tasks/${processInfo.id}` : '/tasks';
    const path = apiCall;
    HttpService.makeCallToBackend({
      path,
      httpMethod: 'GET',
      successCallback: processResult,
    });

    return true;
  };

  /** TanStack (React Query) trigger to do it's SWR state/cache thing */
  useQuery({
    queryKey: [apiCall, processInfo.id],
    queryFn: () => getTaskCollection(),
  });

  return {
    completedTasks,
    loading,
  };
}
