import { useTranslation } from 'react-i18next';

export default function ServidorForaDoAr() {
  const { t } = useTranslation();

  return (
    <div>
      <h1>{t('server_error_title')}</h1>
      <p>{t('server_error_message')}</p>
    </div>
  );
}