import { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import ProcessInstanceService from '../services/ProcessInstanceService';

export default function ProcessInstanceShortLink() {
  const params = useParams();
  const navigate = useNavigate();

  useEffect(() => {
    ProcessInstanceService.navigate({
      processInstanceId: parseInt(params.process_instance_id || '0', 10),
    });
  }, [params.process_instance_id, navigate]);

  return null;
}
