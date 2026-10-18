import { useParams } from 'react-router-dom';
import { usePermissionFetcher } from './PermissionService';

// Returns the process instance show page url, or null if the user may not view that page.
export default function useProcessInstanceShowPageUrl(variant: string) {
  const params = useParams();
  const variantPrefix = variant === 'all' ? '' : '/for-me';
  const url = `/process-instances${variantPrefix}/${params.process_model_id}/${params.process_instance_id}`;
  // the page url mirrors the api path that serves it
  const apiPath = `/v1.0${url}`;
  const { ability, permissionsLoaded } = usePermissionFetcher({
    [apiPath]: ['GET'],
  });
  return {
    processInstanceShowPageUrl: ability.can('GET', apiPath) ? url : null,
    permissionsLoaded,
  };
}
