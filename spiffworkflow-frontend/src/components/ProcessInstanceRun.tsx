import { useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button,
  // @ts-ignore
} from '@carbon/react';
import { ProcessModel } from '../interfaces';
import HttpService from '../services/HttpService';
import ErrorContext from '../contexts/ErrorContext';
import { modifyProcessIdentifierForPathParam } from '../helpers';

type OwnProps = {
  processModel: ProcessModel;
  onSuccessCallback: Function;
  className?: string;
};

export default function ProcessInstanceRun({
  processModel,
  onSuccessCallback,
  className,
}: OwnProps) {
  const navigate = useNavigate();
  const setErrorMessage = (useContext as any)(ErrorContext)[1];
  const modifiedProcessModelId = modifyProcessIdentifierForPathParam(
    processModel.id
  );

  const onProcessInstanceRun = (processInstance: any) => {
    // FIXME: ensure that the task is actually for the current user as well
    const processInstanceId = (processInstance as any).id;
    const nextTask = (processInstance as any).next_task;
    if (nextTask && nextTask.state === 'READY') {
      navigate(`/tasks/${processInstanceId}/${nextTask.id}`);
    }
    onSuccessCallback(processInstance);
  };

  const processModelRun = (processInstance: any) => {
    setErrorMessage(null);
    HttpService.makeCallToBackend({
      path: `/process-instances/${processInstance.id}/run`,
      successCallback: onProcessInstanceRun,
      failureCallback: setErrorMessage,
      httpMethod: 'POST',
    });
  };

  const processInstanceCreateAndRun = () => {
    HttpService.makeCallToBackend({
      path: `/process-models/${modifiedProcessModelId}/process-instances`,
      successCallback: processModelRun,
      httpMethod: 'POST',
    });
  };

  return (
    <Button
      onClick={processInstanceCreateAndRun}
      variant="primary"
      className={className}
    >
      Run
    </Button>
  );
}
