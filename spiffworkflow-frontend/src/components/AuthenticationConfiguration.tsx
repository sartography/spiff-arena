import { Editor } from '@monaco-editor/react';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import HttpService from '../services/HttpService';

export default function AuthenticationConfiguration() {
  const { t } = useTranslation();

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
      <Button variant="contained" onClick={() => saveAuthConfig()}>
        {t('save')}
      </Button>
      <br />
      <br />
      <h2>{t('local_configuration')}</h2>
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
