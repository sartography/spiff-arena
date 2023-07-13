import { useEffect, useState } from 'react';
import {
  Dropdown,
  Table,
  TableHead,
  TableHeader,
  TableRow,
} from '@carbon/react';
import { TableBody, TableCell } from '@mui/material';
import { useSearchParams } from 'react-router-dom';
import HttpService from '../services/HttpService';
import { DataStore, DataStoreRecords, PaginationObject } from '../interfaces';
import PaginationForTable from './PaginationForTable';
import { getPageInfoFromSearchParams } from '../helpers';

export default function DataStoreList() {
  const [dataStores, setDataStores] = useState<DataStore[]>([]);
  const [dataStore, setDataStore] = useState<DataStore | null>(null);
  const [pagination, setPagination] = useState<PaginationObject | null>(null);
  const [results, setResults] = useState<any[]>([]);
  const [searchParams, setSearchParams] = useSearchParams();

  useEffect(() => {
    HttpService.makeCallToBackend({
      path: `/data-stores`,
      successCallback: (newStores: DataStore[]) => {
        setDataStores(newStores);
      },
    });
  }, []); // Do this once so we have a list of data stores to select from.

  useEffect(() => {
    const { page, perPage } = getPageInfoFromSearchParams(
      searchParams,
      10,
      1,
      'datastore'
    );
    console.log();
    const dataStoreType = searchParams.get('type') || '';
    const dataStoreName = searchParams.get('name') || '';

    if (dataStoreType === '' || dataStoreName === '') {
      return;
    }
    if (dataStores && dataStoreName && dataStoreType) {
      dataStores.forEach((ds) => {
        if (ds.name === dataStoreName && ds.type === dataStoreType) {
          setDataStore(ds);
        }
      });
    }
    const queryParamString = `per_page=${perPage}&page=${page}`;
    HttpService.makeCallToBackend({
      path: `/data-stores/${dataStoreType}/${dataStoreName}?${queryParamString}`,
      successCallback: (response: DataStoreRecords) => {
        setResults(response.results);
        setPagination(response.pagination);
      },
    });
  }, [dataStores, searchParams]);

  const getTable = () => {
    if (results.length === 0) {
      return null;
    }
    const firstResult = results[0];
    console.log('Results', results);
    const tableHeaders: any[] = [];
    const keys = Object.keys(firstResult);
    keys.forEach((key) => tableHeaders.push(<TableHeader>{key}</TableHeader>));

    return (
      <Table striped bordered>
        <TableHead>
          <TableRow>{tableHeaders}</TableRow>
        </TableHead>
        <TableBody>
          {results.map((object) => {
            return (
              <TableRow>
                {keys.map((key) => {
                  return <TableCell>{object[key]}</TableCell>;
                })}
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    );
  };

  const { page, perPage } = getPageInfoFromSearchParams(
    searchParams,
    10,
    1,
    'datastore'
  );
  return (
    <>
      <Dropdown
        id="data-store-dropdown"
        titleText="Select Data Store"
        helperText="Select the data store you wish to view"
        label="Please select a data store"
        items={dataStores}
        selectedItem={dataStore}
        itemToString={(ds: DataStore) => (ds ? `${ds.name} (${ds.type})` : '')}
        onChange={(event: any) => {
          setDataStore(event.selectedItem);
          searchParams.set('datastore_page', '1');
          searchParams.set('datastore_per_page', '10');
          searchParams.set('type', event.selectedItem.type);
          searchParams.set('name', event.selectedItem.name);
          setSearchParams(searchParams);
        }}
      />
      <PaginationForTable
        page={page}
        perPage={perPage}
        pagination={pagination}
        tableToDisplay={getTable()}
        paginationQueryParamPrefix="datastore"
      />
    </>
  );
}
