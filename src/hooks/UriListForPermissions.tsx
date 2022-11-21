import { useParams } from 'react-router-dom';

export const useUriListForPermissions = () => {
  const params = useParams();
  const targetUris = {
    authenticationListPath: `/v1.0/authentications`,
    messageInstanceListPath: '/v1.0/messages',
    processGroupListPath: '/v1.0/process-groups',
    processGroupShowPath: `/v1.0/process-groups/${params.process_group_id}`,
    processInstanceActionPath: `/v1.0/process-models/${params.process_model_id}/process-instances`,
    processInstanceListPath: '/v1.0/process-instances',
    processModelCreatePath: `/v1.0/process-models/${params.process_group_id}`,
    processModelFileCreatePath: `/v1.0/process-models/${params.process_model_id}/files`,
    processModelFileShowPath: `/v1.0/process-models/${params.process_model_id}/files/${params.file_name}`,
    processModelShowPath: `/v1.0/process-models/${params.process_model_id}`,
    secretListPath: `/v1.0/secrets`,
  };

  return { targetUris };
};
