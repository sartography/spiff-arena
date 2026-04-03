import CodeMirror from '@uiw/react-codemirror';
import { json } from '@codemirror/lang-json';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import { useTheme } from '@mui/material';
import HttpService from '../services/HttpService';

export default function AuthenticationConfiguration() {
  const { t } = useTranslation();
  const theme = useTheme();
  const codeMirrorTheme = theme.palette.mode === 'dark' ? 'dark' : 'light';

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
      <CodeMirror
        height={'600px'}
        width="auto"
        value={authConfig || ''}
        extensions={[json()]}
        onChange={(value) => setAuthConfig(value || '')}
        theme={codeMirrorTheme}
      />
    </>
  );
}
