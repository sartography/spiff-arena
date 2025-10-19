import { useTranslation } from 'react-i18next';
import ConfirmButton from '../components/ConfirmButton';
import HttpService from '../services/HttpService';
import { DataStore } from '../interfaces';
import { useNavigate } from 'react-router-dom';

export default function DataStoreButtons({
  dataStore,
}: {
  dataStore: DataStore;
}) {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const navigateToDataStores = (_result: any) => {
    navigate(`/data-stores`);
  };

  const clearDataStore = () => {
    HttpService.makeCallToBackend({
      path: `/data-stores/${dataStore.type}/${dataStore.id}/items?location=${dataStore.location}`,
      httpMethod: 'DELETE',
      successCallback: navigateToDataStores,
    });
  };

  const deleteDataStore = () => {
    HttpService.makeCallToBackend({
      path: `/data-stores/${dataStore.type}/${dataStore.id}?process_group_identifier=${dataStore.location}`,
      httpMethod: 'DELETE',
      successCallback: navigateToDataStores,
    });
  };

  return (
    <>
      <ConfirmButton
        buttonLabel={t('clear')}
        onConfirmation={clearDataStore}
      />{' '}
      <ConfirmButton
        buttonLabel={t('delete')}
        onConfirmation={deleteDataStore}
      />
    </>
  );
}
