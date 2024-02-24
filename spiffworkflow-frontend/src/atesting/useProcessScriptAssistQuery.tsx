import { useEffect, useState } from 'react';
import HttpService from '../services/HttpService';

const useProcessScriptAssistMessage = () => {
  const [scriptAssistQuery, setScriptAssistQuery] = useState('');
  const [scriptAssistResult, setScriptAssistResult] = useState('');

  useEffect(() => {
    console.log(scriptAssistQuery);
    const handleResponse = (response: any) => {
      console.log(response);
      setScriptAssistResult(response.ok);
      setScriptAssistQuery('');
    };

    if (scriptAssistQuery) {
      /**
       * Note that the backend has guardrails to prevent requests other than python scripts.
       * See script_assist_controller.py
       */
      const query = `Create a python script that ${scriptAssistQuery}`;
      console.log(query);
      HttpService.makeCallToBackend({
        httpMethod: 'POST',
        path: `/script-assist/process-message`,
        postBody: scriptAssistQuery,
        successCallback: handleResponse,
      });
    }
  }, [scriptAssistQuery, setScriptAssistQuery, scriptAssistResult]);

  return {
    setScriptAssistQuery,
    scriptAssistResult,
  };
};

export default useProcessScriptAssistMessage;
