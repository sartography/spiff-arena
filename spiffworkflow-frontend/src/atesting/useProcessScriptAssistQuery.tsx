import { useEffect, useState } from 'react';
import axios from 'axios';
import { BACKEND_BASE_URL } from '../config';

const useProcessScriptAssistMessage = () => {
  const [scriptAssistQuery, setScriptAssistQuery] = useState('');
  const [scriptAssistResult, setScriptAssistResult] = useState('');

  const client = axios.create({
    baseURL: BACKEND_BASE_URL,
  });

  useEffect(() => {
    if (scriptAssistQuery) {
      client.get('/process-script-assist').then((response) => {
        console.log('RESPONSE', response);
        setScriptAssistResult(response.data.enabled);
      });
    }
  }, [client, scriptAssistQuery, setScriptAssistQuery, scriptAssistResult]);

  return {
    setScriptAssistQuery,
    scriptAssistResult,
  };
};

export default useProcessScriptAssistMessage;
