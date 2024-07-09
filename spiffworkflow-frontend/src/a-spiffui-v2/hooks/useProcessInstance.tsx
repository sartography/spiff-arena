import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import HttpService from '../../services/HttpService';

/**
 * Grab processInstances using HttpService from the Spiff API.
 * TODO: We'll need to allow appending the path to hit different endpoints.
 * Right now we're only using "for-me"
 */
export default function useProcessInstance() {
  // TODO: ProcessInstance type didn't seem right
  // Find out and remove "any"
  const [processInstance, setProcessInstance] = useState<Record<string, any>>(
    {},
  );
  const [processInstanceId, setProcessInstanceId] = useState(0);
  const [loading, setLoading] = useState(false);

  const processResult = (result: any[]) => {
    setProcessInstance(result);
    setLoading(false);
  };

  const getProcessInstance = async () => {
    if (!processInstanceId) {
      setLoading(true);
      const path = `/tasks?process_instance_id=11`;
      HttpService.makeCallToBackend({
        path,
        successCallback: processResult,
      });
    }

    // return required for Tanstack query
    return true;
  };

  useQuery({
    queryKey: ['/tasks?process_instance_id=11', processInstanceId],
    queryFn: () => getProcessInstance(),
  });

  return {
    setProcessInstanceId,
    processInstance,
    loading,
  };
}
