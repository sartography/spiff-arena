import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import Typography from '@mui/material/Typography';
import { useTranslation } from 'react-i18next';
import DataStoreForm from '../components/DataStoreForm';
import { DataStore, HotCrumbItem } from '../interfaces';
import { setPageTitle } from '../helpers';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';

export default function DataStoreNew() {
  const [searchParams] = useSearchParams();
  const parentGroupId = searchParams.get('parentGroupId');
  const [dataStore, setDataStore] = useState<DataStore>({
    id: '',
    name: '',
    type: '',
    schema: '{}',
    description: '',
  });

  const { t } = useTranslation();
  useEffect(() => {
    setPageTitle([t('new_data_store')]);
  }, [t]);

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
        {t('add_data_store')}
      </Typography>
      <DataStoreForm
        mode="new"
        dataStore={dataStore}
        setDataStore={setDataStore}
      />
    </>
  );
}
