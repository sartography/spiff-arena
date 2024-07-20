import { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import HttpService from '../../../services/HttpService';
import useAPIError from '../../../hooks/UseApiError';
import { modifyProcessIdentifierForPathParam } from '../../../helpers';
import { ProcessInstance } from '../../../interfaces';

export default function StartProcessInstance() {
  const { processModelId } = useParams<{ processModelId: string }>();
  const navigate = useNavigate();
  const { addError } = useAPIError();

  const modifiedProcessModelId = modifyProcessIdentifierForPathParam(
    processModelId || '',
  );

  const onProcessInstanceRun = (processInstance: ProcessInstance) => {
    const processInstanceId = processInstance.id;
    if (processInstance.process_model_uses_queued_execution) {
      navigate(
        `/process-instances/for-me/${modifiedProcessModelId}/${processInstanceId}/progress`,
      );
    } else {
      navigate(
        `/process-instances/for-me/${modifiedProcessModelId}/${processInstanceId}/interstitial`,
      );
    }
  };

  const processModelRun = (processInstance: ProcessInstance) => {
    HttpService.makeCallToBackend({
      path: `/process-instances/${modifiedProcessModelId}/${processInstance.id}/run`,
      successCallback: onProcessInstanceRun,
      failureCallback: (result: any) => {
        addError(result);
      },
      httpMethod: 'POST',
    });
  };

  const processInstanceCreateAndRun = () => {
    HttpService.makeCallToBackend({
      path: `/v1.0/process-instances/${modifiedProcessModelId}`,
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

  return <p>Starting Process...</p>;
}
