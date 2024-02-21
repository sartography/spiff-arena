import { useEffect, useState } from 'react';
import axios from 'axios';
import { BACKEND_BASE_URL } from '../config';

const useProcessScriptAssistMessage = () => {
  const [scriptAssistMessage, setScriptAssistMessage] = useState('');

  const client = axios.create({
    baseURL: BACKEND_BASE_URL,
  });

  useEffect(() => {
    if (scriptAssistMessage) {
      client.get('/process-script-assist').then((response) => {
        console.log('RESPONSE', response);
        setScriptAssistMessage(response.data.enabled);
      });
    }
  }, [client, scriptAssistMessage, setScriptAssistMessage]);

  return {
    scriptAssistMessage,
    setScriptAssistMessage,
  };
};

export default useProcessScriptAssistMessage;
