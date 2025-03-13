import React from 'react';
import { Typography } from '@mui/material';
import DataStoreListTable from '../components/DataStoreListTable';
import { setPageTitle } from '../helpers';

export default function DataStoreList() {
  setPageTitle(['Data Stores']);
  return (
    <>
      <Typography variant="h1" sx={{ mb: 2 }}>
        Data Stores
      </Typography>
      <DataStoreListTable />
    </>
  );
}
