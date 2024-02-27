import { useEffect, useState } from 'react';
import HttpService from '../services/HttpService';

/**
 * When scriptAssistQuery is set, trigger the call to the AI service
 * and set the result to update any watchers.
 */
const useProcessScriptAssistMessage = () => {
  const [scriptAssistQuery, setScriptAssistQuery] = useState('');
  const [scriptAssistResult, setScriptAssistResult] = useState('');

  useEffect(() => {
    const handleResponse = (response: Record<string, any>) => {
      setScriptAssistResult(response.ok);
      setScriptAssistQuery('');
    };

    /** Possibly make this check more robust, depending on what we see in use. */
    if (scriptAssistQuery) {
      /**
       * Note that the backend has guardrails to prevent requests other than python scripts.
       * See script_assist_controller.py
       */
      HttpService.makeCallToBackend({
        httpMethod: 'POST',
        path: `/script-assist/process-message`,
        postBody: scriptAssistQuery.trim(),
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
