import { useParams } from 'react-router-dom';

export const useUriListForPermissions = () => {
  const params = useParams();
  const targetUris = {
    processGroupListPath: `/v1.0/process-groups`,
    processGroupShowPath: `/v1.0/process-groups/${params.process_group_id}`,
    processModelListPath: `/v1.0/process-models`,
    processModelShowPath: `/v1.0/process-models/${params.process_model_id}`,
    processInstanceListPath: `/v1.0/process-instances`,
    processInstanceActionPath: `/v1.0/process-models/${params.process_model_id}/process-instances`,
  };

  return { targetUris };
};
