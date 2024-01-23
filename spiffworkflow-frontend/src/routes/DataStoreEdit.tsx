import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useSearchParams } from 'react-router-dom';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import DataStoreForm from '../components/DataStoreForm';
import { DataStore, HotCrumbItem } from '../interfaces';
import { setPageTitle } from '../helpers';
import HttpService from '../services/HttpService';

export default function DataStoreEdit() {
  const params = useParams();
  const [searchParams] = useSearchParams();
  const parentGroupId = searchParams.get('parentGroupId');
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
      result.schema = JSON.stringify(result.schema);
      setDataStore(result);
    };

      let queryParams = `?process_group_identifier=${parentGroupId}`;
      HttpService.makeCallToBackend({
      // TODO: don't hardcode json
      // TODO: is making infinite calls
        path: `/data-stores/json/${dataStoreIdentifier}${queryParams}`,
        successCallback: setDataStoreFromResult,
      });

  }, [dataStoreIdentifier, parentGroupId]);


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
