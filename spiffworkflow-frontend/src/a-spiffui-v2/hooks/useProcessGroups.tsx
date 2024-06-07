import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
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
  const [processGroups, setProcessGroups] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(false);

  const processResult = (result: Record<string, any>[]) => {
    setProcessGroups({ ...result });
    setLoading(false);
  };

  const path = '/process-groups';
  const getProcessGroups = async () => {
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
    queryFn: () => getProcessGroups(),
  });

  return {
    processGroups,
    loading,
  };
}
