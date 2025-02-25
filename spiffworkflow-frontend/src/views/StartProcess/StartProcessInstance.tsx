import { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import HttpService from '../../services/HttpService';
import useAPIError from '../../hooks/UseApiError';
import { modifyProcessIdentifierForPathParam } from '../../helpers';
import { ProcessInstance } from '../../interfaces';

// TODO: reimplment as a component that adds a global error on failure similar to the ProcessInstanceRun component dos it
export default function StartProcessInstance() {
  const { modifiedProcessModelId } = useParams<{
    modifiedProcessModelId: string;
  }>();
  const navigate = useNavigate();
  const { addError } = useAPIError();

  const modifiedProcessModelIdParam = modifyProcessIdentifierForPathParam(
    modifiedProcessModelId || '',
  );

  const onProcessInstanceRun = (processInstance: ProcessInstance) => {
    const processInstanceId = processInstance.id;
    if (processInstance.process_model_uses_queued_execution) {
      navigate(
        `/process-instances/for-me/${modifiedProcessModelIdParam}/${processInstanceId}/progress`,
      );
    } else {
      navigate(
        `/process-instances/for-me/${modifiedProcessModelIdParam}/${processInstanceId}/interstitial`,
      );
    }
  };

  const processModelRun = (processInstance: ProcessInstance) => {
    HttpService.makeCallToBackend({
      path: `/process-instances/${modifiedProcessModelIdParam}/${processInstance.id}/run`,
      successCallback: onProcessInstanceRun,
      failureCallback: (result: any) => {
        addError(result);
      },
      httpMethod: 'POST',
    });
  };

  const processInstanceCreateAndRun = () => {
    HttpService.makeCallToBackend({
      path: `/v1.0/process-instances/${modifiedProcessModelIdParam}`,
      successCallback: processModelRun,
      failureCallback: (result: any) => {
        addError(result);
      },
      httpMethod: 'POST',
    });
  };

  useEffect(() => {
    processInstanceCreateAndRun();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return null;
}
