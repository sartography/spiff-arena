import React from 'react';
import DataStoreListTable from '../components/DataStoreListTable';
import { setPageTitle } from '../helpers';

export default function DataStoreList() {
  setPageTitle(['Data Stores']);
  return (
    <>
      <h1>Data Stores</h1>
      <DataStoreListTable />
    </>
  );
}
