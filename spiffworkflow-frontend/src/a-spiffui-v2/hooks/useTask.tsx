import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import HttpService from '../../services/HttpService';

/**
 * Grab a single Task using HttpService from the Spiff API.
 */
export default function useTask() {
  const [task, setTask] = useState<Record<string, any>>({});
  const [taskGuid, setTaskGuid] = useState(0);
  const [loading, setLoading] = useState(false);

  const processResult = (result: any[]) => {
    setTask(result);
    setLoading(false);
  };

  const path = `/task-data/{modified_process_model_identifier}/{process_instance_id}/{task_id}`;
  const getProcessInstance = async () => {
    if (!taskGuid) {
      setLoading(true);
      HttpService.makeCallToBackend({
        path,
        successCallback: processResult,
      });
    }

    // return required for Tanstack query
    return true;
  };

  useQuery({
    queryKey: [path, taskGuid],
    queryFn: () => getProcessInstance(),
  });

  return {
    setTaskGuid,
    task,
    loading,
  };
}
