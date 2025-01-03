import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import Breadcrumbs from '@mui/material/Breadcrumbs';
import Typography from '@mui/material/Typography';
import Link from '@mui/material/Link';
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
      <Breadcrumbs aria-label="breadcrumb">
        {hotCrumbs.map((crumb, index) => (
          <Link
            key={index}
            color="inherit"
            href={typeof crumb === 'string' ? crumb[1] : ''}
          >
            {typeof crumb === 'string' ? crumb[0] : crumb.entityToExplode}
          </Link>
        ))}
      </Breadcrumbs>
      <Typography variant="h4" component="h1" gutterBottom>
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
