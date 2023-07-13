import { useMemo } from 'react';
import { useParams } from 'react-router-dom';

export const useUriListForPermissions = () => {
  const params = useParams();
  const targetUris = useMemo(() => {
    return {
      authenticationListPath: `/v1.0/authentications`,
      messageInstanceListPath: '/v1.0/messages',
      dataStoreListPath: '/v1.0/data-stores',
      processGroupListPath: '/v1.0/process-groups',
      processGroupShowPath: `/v1.0/process-groups/${params.process_group_id}`,
      processInstanceActionPath: `/v1.0/process-instances/${params.process_model_id}/${params.process_instance_id}`,
      processInstanceCompleteTaskPath: `/v1.0/task-complete/${params.process_model_id}/${params.process_instance_id}`,
      processInstanceCreatePath: `/v1.0/process-instances/${params.process_model_id}`,
      processInstanceErrorEventDetails: `/v1.0/event-error-details/${params.process_model_id}/${params.process_instance_id}`,
      processInstanceListPath: '/v1.0/process-instances',
      processInstanceListForMePath: `/v1.0/process-instances/for-me`,
      processInstanceLogListPath: `/v1.0/logs/${params.process_model_id}/${params.process_instance_id}`,
      processInstanceReportListPath: '/v1.0/process-instances/reports',
      processInstanceResetPath: `/v1.0/process-instance-reset/${params.process_model_id}/${params.process_instance_id}`,
      processInstanceResumePath: `/v1.0/process-instance-resume/${params.process_model_id}/${params.process_instance_id}`,
      processInstanceSendEventPath: `/v1.0/send-event/${params.process_model_id}/${params.process_instance_id}`,
      processInstanceSuspendPath: `/v1.0/process-instance-suspend/${params.process_model_id}/${params.process_instance_id}`,
      processInstanceTaskAssignPath: `/v1.0/task-assign/${params.process_model_id}/${params.process_instance_id}`,
      processInstanceTaskDataPath: `/v1.0/task-data/${params.process_model_id}/${params.process_instance_id}`,
      processInstanceTaskListForMePath: `/v1.0/process-instances/for-me/${params.process_model_id}/${params.process_instance_id}/task-info`,
      processInstanceTaskListPath: `/v1.0/process-instances/${params.process_model_id}/${params.process_instance_id}/task-info`,
      processInstanceTerminatePath: `/v1.0/process-instance-terminate/${params.process_model_id}/${params.process_instance_id}`,
      processModelCreatePath: `/v1.0/process-models/${params.process_group_id}`,
      processModelFileCreatePath: `/v1.0/process-models/${params.process_model_id}/files`,
      processModelFileShowPath: `/v1.0/process-models/${params.process_model_id}/files/${params.file_name}`,
      processModelPublishPath: `/v1.0/process-model-publish/${params.process_model_id}`,
      processModelShowPath: `/v1.0/process-models/${params.process_model_id}`,
      processModelTestsPath: `/v1.0/process-model-tests/${params.process_model_id}`,
      secretListPath: `/v1.0/secrets`,
      userSearch: `/v1.0/users/search`,
      userExists: `/v1.0/users/exists/by-username`,
    };
  }, [params]);

  return { targetUris };
};
