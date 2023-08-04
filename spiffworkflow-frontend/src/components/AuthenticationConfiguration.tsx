import Editor from '@monaco-editor/react';
import { useEffect, useState } from 'react';
import HttpService from '../services/HttpService';

export default function AuthenticationConfiguration() {
  const [authConfig, setAuthConfig] = useState('');

  useEffect(() => {
    HttpService.makeCallToBackend({
      path: '/authentication/configuration',
      successCallback: (newAuthConfig: string) => {
        setAuthConfig(JSON.stringify(newAuthConfig, null, 4));
      },
    });
  }, []);

  return (
    <>
      <p>Local Configuration</p>
      <Editor
        height={600}
        width="auto"
        defaultLanguage="json"
        defaultValue={authConfig || ''}
        onChange={(_) => null}
      />
    </>
  );
}
