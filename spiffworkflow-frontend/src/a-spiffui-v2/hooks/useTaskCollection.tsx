import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import HttpService from '../../services/HttpService';

/**
 * Grab tasks using the existing HttpService.ts and the Spiff API.
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

  /** Query function to get tasks from the backend (must return value for React Query) */
  const processResult = (result: Record<string, any>[]) => {
    setTaskCollection({ ...result });
    setLoading(false);
  };

  // TODO: Currently, the API endpoint for this is an SSE endpoint, so we can't use the HttpService.
  // We'll need to refactor this to use the SSE service, or change the API to return a RESTful response.
  // So for now, we're just getting "all" and doing PI id filtering client-side, which is not ideal.
  // const path = processInfo?.id ? `/tasks/${processInfo.id}` : '/tasks';
  const path = '/tasks';
  const getTaskCollection = async () => {
    setLoading(true);
    HttpService.makeCallToBackend({
      path,
      httpMethod: 'GET',
      successCallback: processResult,
    });

    // return required for Tanstack query
    return true;
  };

  useQuery({
    queryKey: [path, processInfo],
    queryFn: () => getTaskCollection(),
  });

  return {
    taskCollection,
    loading,
  };
}
