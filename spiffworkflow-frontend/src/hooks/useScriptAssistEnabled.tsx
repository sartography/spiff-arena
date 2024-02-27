import { useEffect, useState } from 'react';
import HttpService from '../services/HttpService';

/** Basic fetcher for the env value from the backend */
const useScriptAssistEnabled = () => {
  const [scriptAssistEnabled, setScriptAssistEnabled] = useState(null);

  useEffect(() => {
    if (scriptAssistEnabled === null) {
      const handleResponse = (response: any) => {
        setScriptAssistEnabled(response.ok);
      };

      HttpService.makeCallToBackend({
        path: `/script-assist/enabled`,
        successCallback: handleResponse,
      });
    }
  }, [scriptAssistEnabled]);

  return {
    scriptAssistEnabled,
  };
};

export default useScriptAssistEnabled;
