import { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import useProcessInstanceNavigate from '../hooks/useProcessInstanceNavigate';

export default function ProcessInstanceShortLink() {
  const params = useParams();
  const { navigateToInstance } = useProcessInstanceNavigate();

  useEffect(() => {
    navigateToInstance({
      processInstanceId: parseInt(params.process_instance_id || '0', 10),
    });
  }, [params.process_instance_id, navigateToInstance]);

  return null;
}
