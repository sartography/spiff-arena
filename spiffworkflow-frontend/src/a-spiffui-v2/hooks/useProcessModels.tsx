import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import HttpService from '../../services/HttpService';

/**
 * Grab Process Models using HttpService from the Spiff API.
 * TODO: We'll need to allow appending the path to hit different endpoints.
 * Right now we're just grabbing them all
 */
export default function useProcessModels({
  processInfo,
}: {
  processInfo: Record<string, any>;
}) {
  const [processModels, setProcessModels] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(false);

  const processResult = (result: Record<string, any>[]) => {
    setProcessModels({ ...result });
    setLoading(false);
  };

  const path = '/process-models';
  const getProcessModels = async () => {
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
    queryFn: () => getProcessModels(),
  });

  return {
    processModels,
    loading,
  };
}
