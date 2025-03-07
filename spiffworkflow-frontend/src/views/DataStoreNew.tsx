import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import Typography from '@mui/material/Typography';
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

  useEffect(() => {
    setPageTitle(['New Data Store']);
  }, []);

  const hotCrumbs: HotCrumbItem[] = [['Process Groups', '/process-groups']];
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
        Add Data Store
      </Typography>
      <DataStoreForm
        mode="new"
        dataStore={dataStore}
        setDataStore={setDataStore}
      />
    </>
  );
}
