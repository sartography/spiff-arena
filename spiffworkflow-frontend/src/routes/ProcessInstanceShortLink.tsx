import { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { modifyProcessIdentifierForPathParam } from '../helpers';
import HttpService from '../services/HttpService';
import { ProcessInstance } from '../interfaces';

export default function ProcessInstanceShortLink() {
  const params = useParams();
  const navigate = useNavigate();

  useEffect(() => {
    const handleProcessInstanceNavigation = (result: any) => {
      const processInstance: ProcessInstance = result.process_instance;
      let path = '/process-instances/';
      if (result.uri_type === 'for-me') {
        path += 'for-me/';
      }
      path += `${modifyProcessIdentifierForPathParam(
        processInstance.process_model_identifier
      )}/${processInstance.id}`;
      navigate(path);
    };

    HttpService.makeCallToBackend({
      path: `/process-instances/find-by-id/${params.process_instance_id}`,
      successCallback: handleProcessInstanceNavigation,
    });
  }, [params.process_instance_id, navigate]);

  return null;
}
