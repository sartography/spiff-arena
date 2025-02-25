import { useEffect, useState } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
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
  useEffect(() => {
    setPageTitle(['Edit Data Store']);
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
      <h1>Edit Data Store</h1>
      <DataStoreForm
        mode="edit"
        dataStore={dataStore}
        setDataStore={setDataStore}
      />
    </>
  );
}
