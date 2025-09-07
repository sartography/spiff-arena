import { useTranslation } from 'react-i18next';

export default function FrontendAccessDenied() {
  const { t } = useTranslation();
  return (
    <div>
      <h1>{t('frontend_access_denied_title')}</h1>
      <p>{t('frontend_access_denied_message')}</p>
    </div>
  );
}