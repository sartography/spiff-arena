import Editor from '@monaco-editor/react';
import { useEffect, useState } from 'react';
import { Button } from '@carbon/react';
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

  const saveAuthConfig = () => {
    HttpService.makeCallToBackend({
      path: '/authentication/configuration',
      successCallback: () => {
        window.location.reload();
      },
      httpMethod: 'PUT',
      postBody: { value: authConfig },
    });
  };

  return (
    <>
      <Button onClick={() => saveAuthConfig()}>Save</Button>
      <br />
      <br />
      <h2>Local Configuration</h2>
      <br />
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
