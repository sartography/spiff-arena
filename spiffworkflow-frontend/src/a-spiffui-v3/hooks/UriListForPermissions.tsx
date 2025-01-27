import { useMemo } from 'react';
import { useParams } from 'react-router-dom';

export const useUriListForPermissions = () => {
  const params = useParams();
  const targetUris = useMemo(() => {
    return {
      authenticationListPath: `/v1.0/authentications`,
      statusPath: `/v1.0/status`,
      messageInstanceListPath: '/v1.0/messages',
      messageModelListPath: `/v1.0/message-models/${params.process_model_id}`,
      dataStoreListPath: '/v1.0/data-stores',
      extensionListPath: '/v1.0/extensions',
      extensionPath: `/v1.0/extensions/${params.page_identifier}`,
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
      processInstanceMigratePath: `/v1.0/process-instance-migrate/${params.process_model_id}/${params.process_instance_id}`,
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
      processModelTestsPath: `/v1.0/process-model-tests/run/${params.process_model_id}`,
      secretListPath: `/v1.0/secrets`,
      secretShowPath: `/v1.0/secrets/${params.secret_identifier}`,
      secretShowValuePath: `/v1.0/secrets/show-value/${params.secret_identifier}`,
      userSearch: `/v1.0/users/search`,
      userExists: `/v1.0/users/exists/by-username`,
    };
  }, [
    params.secret_identifier,
    params.file_name,
    params.page_identifier,
    params.process_group_id,
    params.process_instance_id,
    params.process_model_id,
  ]);

  return { targetUris };
};
