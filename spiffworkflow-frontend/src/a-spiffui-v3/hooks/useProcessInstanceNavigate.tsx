import { useNavigate } from 'react-router-dom';
import { modifyProcessIdentifierForPathParam } from '../helpers';
import { ProcessInstance } from '../interfaces';
import HttpService from '../services/HttpService';

type OwnProps = {
  processInstanceId: number;
  suffix?: string;
};
export default function useProcessInstanceNavigate() {
  const navigate = useNavigate();

  const handleProcessInstanceNavigation = (
    result: any,
    processInstanceId: number,
    suffix: string | undefined,
  ) => {
    const processInstanceResult: ProcessInstance = result.process_instance;
    let path = '/process-instances';
    if (result.uri_type === 'for-me') {
      path += '/for-me';
    }
    path += `/${modifyProcessIdentifierForPathParam(
      processInstanceResult.process_model_identifier,
    )}/${processInstanceResult.id}`;
    if (suffix !== undefined) {
      path += suffix;
    }
    const queryParams = window.location.search;
    path += queryParams;
    navigate(path);
  };

  const navigateToInstance = ({ processInstanceId, suffix }: OwnProps) => {
    HttpService.makeCallToBackend({
      path: `/process-instances/find-by-id/${processInstanceId}`,
      successCallback: (result: any) =>
        handleProcessInstanceNavigation(result, processInstanceId, suffix),
    });
  };

  return { navigateToInstance };
}
