import { useEffect, useState } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { Typography } from '@mui/material';
import { useTranslation } from 'react-i18next';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import DataStoreForm from '../components/DataStoreForm';
import { DataStore, HotCrumbItem } from '../interfaces';
import { setPageTitle } from '../helpers';
import HttpService from '../services/HttpService';

export default function DataStoreEdit() {
  const params = useParams();
  const [searchParams] = useSearchParams();
  const parentGroupId = searchParams.get('parentGroupId');
  const dataStoreType = searchParams.get('type');
  const dataStoreIdentifier = params.data_store_identifier;
  const [dataStore, setDataStore] = useState<DataStore>({
    id: '',
    name: '',
    type: '',
    schema: '',
    description: '',
  });
  const { t } = useTranslation();
  useEffect(() => {
    setPageTitle([t('edit_data_store')]);
  }, []);

  useEffect(() => {
    const setDataStoreFromResult = (result: any) => {
      const schema = JSON.stringify(result.schema);
      setDataStore({ ...result, schema });
    };

    const queryParams = `?process_group_identifier=${parentGroupId}`;
    HttpService.makeCallToBackend({
      path: `/data-stores/${dataStoreType}/${dataStoreIdentifier}${queryParams}`,
      successCallback: setDataStoreFromResult,
    });
  }, [dataStoreIdentifier, parentGroupId, dataStoreType]);

  const hotCrumbs: HotCrumbItem[] = [[t('process_groups'), '/process-groups']];
  if (parentGroupId) {
    hotCrumbs.push({
      entityToExplode: parentGroupId,
      entityType: 'process-group-id',
      linkLastItem: true,
    });
  }

  return (
    <>
      <ProcessBreadcrumb hotCrumbs={hotCrumbs} />
      <Typography variant="h1" gutterBottom>
        {t('edit_data_store')}
      </Typography>
      <DataStoreForm
        mode="edit"
        dataStore={dataStore}
        setDataStore={setDataStore}
      />
    </>
  );
}
