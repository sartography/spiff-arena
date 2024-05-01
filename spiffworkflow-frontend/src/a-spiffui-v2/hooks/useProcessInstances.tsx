import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import HttpService from '../../services/HttpService';
import { ReportMetadata } from '../../interfaces';

export default function useProcessInstances() {
  // TODO: ProcessInstance type didn't seem right
  // Find out and remove "any"
  const [processInstances, setProcessInstances] = useState<Record<string, any>>(
    {}
  );
  const [loading, setLoading] = useState(true);

  const reportMetadataToUse: ReportMetadata = {
    columns: [],
    filter_by: [],
    order_by: [],
  };

  // TODO: ProcessInstance didn't seem to be the right type
  // Find out and remove "any"
  const processInstancesResult = (result: any[]) => {
    setProcessInstances(result);
    setLoading(false);
  };

  const getProcessInstances = async () => {
    setLoading(true);
    HttpService.makeCallToBackend({
      path: '/process-instances/for-me?per_page=100&page=1',
      httpMethod: 'POST',
      successCallback: processInstancesResult,
      postBody: {
        report_metadata: reportMetadataToUse,
      },
    });

    /** Query functions used by TanStack Query (React Query)
     * must always return data, but we don't need to use it
     */

    return true;
  };

  /** TanStack (React Query) trigger to do it's SWR state/cache thing */
  useQuery({
    queryKey: ['/process-instances/for-me', processInstances],
    queryFn: () => getProcessInstances(),
  });

  return {
    processInstances,
    loading,
  };
}
