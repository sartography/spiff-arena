import { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Box } from '@carbon/icons-react';
import HttpService from '../../../services/HttpService';
import useAPIError from '../../../hooks/UseApiError';
import { modifyProcessIdentifierForPathParam } from '../../../helpers';
import { ProcessInstance } from '../../../interfaces';

type OwnProps = {
  isMobile: boolean;
};

export default function StartProcessInstance({ isMobile }: OwnProps) {
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
        `/newui/process-instances/for-me/${modifiedProcessModelIdParam}/${processInstanceId}/progress`,
      );
    } else {
      navigate(
        `/newui/process-instances/for-me/${modifiedProcessModelIdParam}/${processInstanceId}/interstitial`,
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

  return (
    <Box
      component="main"
      sx={{
        flexGrow: 1,
        p: 3,
        overflow: 'auto',
        height: isMobile ? 'calc(100vh - 64px)' : '100vh',
        mt: isMobile ? '64px' : 0,
      }}
    >
      <p>Starting Process...</p>
    </Box>
  );
}
