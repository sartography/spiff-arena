import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import HttpService from '../../services/HttpService';
import { ReportMetadata } from '../../interfaces';

/**
 * Grab processInstances using HttpService from the Spiff API.
 * TODO: We'll need to allow appending the path to hit different endpoints.
 * Right now we're only using "for-me"
 */
export default function useProcessInstanceCollection() {
  /**
   * At this point, it seems you change the type of the collection
   * by specifiying this piece of info. (They seem to be the same collection).
   * TODO: Find out what's what here
   */
  type ApiCollectionType = 'all' | 'for-me';
  const [apiCollectionType, setApiCollectionType] =
    useState<ApiCollectionType>('all');
  const [processInstanceCollection, setProcessInstanceCollection] = useState<
    Record<string, any>
  >({});
  const [loading, setLoading] = useState(false);

  const reportMetadataToUse: ReportMetadata = {
    columns: [],
    filter_by: [],
    order_by: [],
  };

  const processResult = (result: any[]) => {
    setProcessInstanceCollection(result);
    setLoading(false);
  };

  const getProcessInstanceCollection = async () => {
    setLoading(true);
    const path = `/process-instances${
      apiCollectionType === 'all' ? '' : `/${apiCollectionType}`
    }?per_page=100&page=1`;
    HttpService.makeCallToBackend({
      path,
      httpMethod: 'POST',
      successCallback: processResult,
      postBody: {
        report_metadata: reportMetadataToUse,
      },
    });

    // return required for Tanstack query
    return true;
  };

  /** TanStack (React Query) trigger to do it's SWR state/cache thing */
  useQuery({
    queryKey: ['/process-instances/for-me', processInstanceCollection],
    queryFn: () => getProcessInstanceCollection(),
  });

  return {
    setApiCollectionType,
    processInstanceCollection,
    loading,
  };
}
