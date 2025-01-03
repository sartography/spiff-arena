import React from 'react';
import DataStoreListTable from '../components/DataStoreListTable';
import { setPageTitle } from '../helpers';
import { Typography } from '@mui/material';

export default function DataStoreList() {
  setPageTitle(['Data Stores']);
  return (
    <>
      <Typography variant="h1">Data Stores</Typography>
      <DataStoreListTable />
    </>
  );
}
