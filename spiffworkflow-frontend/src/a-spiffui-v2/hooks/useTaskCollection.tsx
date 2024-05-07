import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import HttpService from '../../services/HttpService';

/**
 * Grab tasks using HttpService from the Spiff API.
 * TODO: We'll need to allow appending the path to hit different endpoints.
 * Right now we're just grabbing for-me
 */
export default function useTaskCollection() {
  const [taskCollection, setTaskCollection] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(false);

  /**
   * Query function to get process instances from the backend
   * @returns Query functions must return a value, even if it's just true
   */
  const processResult = (result: any[]) => {
    console.log(result);
    setTaskCollection(result);
    setLoading(false);
  };

  const getTaskCollection = async () => {
    setLoading(true);
    const path = '/tasks';
    HttpService.makeCallToBackend({
      path,
      httpMethod: 'GET',
      successCallback: processResult,
    });

    return true;
  };

  /** TanStack (React Query) trigger to do it's SWR state/cache thing */
  useQuery({
    queryKey: ['/tasks', taskCollection],
    queryFn: () => getTaskCollection(),
  });

  return {
    taskCollection,
    loading,
  };
}
