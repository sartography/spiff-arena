import Editor from '@monaco-editor/react';
import { useEffect, useState } from 'react';
import HttpService from '../services/HttpService';
import { Button } from '@carbon/react';

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

  const saveAuthConfig = () => {
    HttpService.makeCallToBackend({
      path: '/authentication/configuration',
      successCallback: () => {},
      httpMethod: 'PUT',
      postBody: { 'value': authConfig },
    });
  };

  return (
    <>
      <h3>Local Configuration</h3>
      <Button onClick={() => saveAuthConfig()}>Save</Button>
      <Editor
        height={600}
        width="auto"
        defaultLanguage="json"
        defaultValue={authConfig || ''}
        onChange={(value) => setAuthConfig(value || '')}
      />
    </>
  );
}
