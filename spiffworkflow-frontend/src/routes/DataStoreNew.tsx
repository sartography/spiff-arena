import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import DataStoreForm from '../components/DataStoreForm';
import { DataStore, HotCrumbItem } from '../interfaces';
import { setPageTitle } from '../helpers';

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
      <h1>Add Data Store</h1>
      <DataStoreForm
        mode="new"
        dataStore={dataStore}
        setDataStore={setDataStore}
      />
    </>
  );
}
