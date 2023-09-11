import React from 'react';
import DataStoreList from '../components/DataStoreList';
import { setPageTitle } from '../helpers';

export default function DataStorePage() {
  setPageTitle(['Data Stores']);
  return (
    <>
      <h1>Data Stores</h1>
      <DataStoreList />
    </>
  );
}
