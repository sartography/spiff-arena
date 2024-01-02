import { modifyProcessIdentifierForPathParam } from '../helpers';
import { ProcessInstance } from '../interfaces';
import HttpService from './HttpService';

type OwnProps = {
  processInstanceId: number;
  suffix?: string;
};
const navigate = ({ processInstanceId, suffix }: OwnProps) => {
  const handleProcessInstanceNavigation = (result: any) => {
    const processInstanceResult: ProcessInstance = result.process_instance;
    let path = '/process-instances';
    if (result.uri_type === 'for-me') {
      path += '/for-me';
    }
    path += `/${modifyProcessIdentifierForPathParam(
      processInstanceResult.process_model_identifier
    )}/${processInstanceResult.id}`;
    if (suffix !== undefined) {
      path += suffix;
    }
    // if we made this into a hook (that returned a function like this, perhaps),
    // we could use useNavigate instead.
    window.location.pathname = path;
  };

  HttpService.makeCallToBackend({
    path: `/process-instances/find-by-id/${processInstanceId}`,
    successCallback: handleProcessInstanceNavigation,
  });
};

const ProcessInstanceService = {
  navigate,
};

export default ProcessInstanceService;
