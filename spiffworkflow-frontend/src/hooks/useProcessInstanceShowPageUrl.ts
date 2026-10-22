import { useQuery } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import { modifyProcessIdentifierForPathParam } from '../helpers';
import { PermissionCheckResponseBody } from '../interfaces';
import HttpService from '../services/HttpService';

export const processInstanceShowPagePath = (
  variant: string,
  modelIdentifier: string,
  instanceId: number | string,
) =>
  `/process-instances${variant === 'all' ? '' : '/for-me'}/${modifyProcessIdentifierForPathParam(modelIdentifier)}/${instanceId}`;

// Check exact paths in one request, including per-instance grants/denies.
// Keep results keyed to the requested pages so pagination/navigation cannot
// reuse permission results for a different set of instances.
export function useProcessInstancePageAccess(pageUrls: string[]) {
  const urls = [...new Set(pageUrls)].sort();
  const { data, isPending } = useQuery({
    queryKey: ['process-instance-page-access', urls],
    enabled: urls.length > 0,
    retry: false,
    queryFn: () =>
      new Promise<PermissionCheckResponseBody>((resolve, reject) => {
        HttpService.makeCallToBackend({
          path: '/permissions-check',
          httpMethod: 'POST',
          postBody: {
            requests_to_check: Object.fromEntries(
              urls.map((url) => [`/v1.0${url}`, ['GET']]),
            ),
          },
          successCallback: resolve,
          failureCallback: reject,
          onUnauthorized: reject,
        });
      }),
  });
  return {
    canReadPage: (url: string) => data?.results[`/v1.0${url}`]?.GET === true,
    permissionsLoaded: urls.length === 0 || !isPending,
  };
}

export default function useProcessInstanceShowPageUrl(variant: string) {
  const params = useParams();
  const url = processInstanceShowPagePath(
    variant,
    params.process_model_id!,
    params.process_instance_id!,
  );
  const { canReadPage, permissionsLoaded } = useProcessInstancePageAccess([
    url,
  ]);
  return {
    processInstanceShowPageUrl: canReadPage(url) ? url : null,
    permissionsLoaded,
  };
}
