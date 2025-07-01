import { useTranslation } from 'react-i18next';

export default function Page404() {
  const { t } = useTranslation();

  return (
    <div>
      <h1>404</h1>
      <p>{t('page_does_not_exist')}</p>
    </div>
  );
}
