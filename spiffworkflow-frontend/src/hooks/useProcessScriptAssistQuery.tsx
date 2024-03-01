import { useEffect, useState } from 'react';
import HttpService from '../services/HttpService';

/**
 * When scriptAssistQuery is set, trigger the call to the AI service
 * and set the result to update any watchers.
 */
const useProcessScriptAssistMessage = () => {
  const [scriptAssistQuery, setScriptAssistQuery] = useState<string>('');
  const [scriptAssistResult, setScriptAssistResult] = useState<Record<
    string,
    any
  > | null>(null);
  const [scriptAssistLoading, setScriptAssistLoading] =
    useState<boolean>(false);

  useEffect(() => {
    const handleResponse = (response: Record<string, any>) => {
      setScriptAssistResult(response);
      setScriptAssistQuery('');
      setScriptAssistLoading(false);
    };

    /** Possibly make this check more robust, depending on what we see in use. */
    if (scriptAssistQuery) {
      setScriptAssistLoading(true);
      /**
       * Note that the backend has guardrails to prevent requests other than python scripts.
       * See script_assist_controller.py
       */
      HttpService.makeCallToBackend({
        httpMethod: 'POST',
        path: `/script-assist/process-message`,
        postBody: { query: scriptAssistQuery.trim() },
        successCallback: handleResponse,
        failureCallback: (error: any) => {
          setScriptAssistResult(error);
          setScriptAssistQuery('');
          setScriptAssistLoading(false);
        },
      });
    }
  }, [scriptAssistQuery, setScriptAssistQuery, scriptAssistResult]);

  return {
    setScriptAssistQuery,
    scriptAssistLoading,
    scriptAssistResult,
  };
};

export default useProcessScriptAssistMessage;
