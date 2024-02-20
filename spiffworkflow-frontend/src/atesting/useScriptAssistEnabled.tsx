import { useEffect, useState } from 'react';
import axios from 'axios';
import { BACKEND_BASE_URL } from '../config';

const useScriptAssistEnabled = () => {
  const [scriptAssistEnabled, setScriptAssistEnabled] = useState(null);

  const client = axios.create({
    baseURL: BACKEND_BASE_URL,
  });

  useEffect(() => {
    if (scriptAssistEnabled === null) {
      client.get('/script-assist').then((response) => {
        console.log('RESPONSE', response);
        setScriptAssistEnabled(response.data.enabled);
      });
    }
  }, [client, scriptAssistEnabled]);

  return {
    scriptAssistEnabled,
  };
};

export default useScriptAssistEnabled;
