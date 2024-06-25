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

export default function DataStoreListTable() {
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
      'datastore',
    );
    const dataStoreType = searchParams.get('type') || '';
    const dataStoreIdentifier = searchParams.get('identifier') || '';
    const dataStoreLocation = searchParams.get('location') || '';

    if (dataStoreType === '' || dataStoreIdentifier === '') {
      return;
    }
    if (dataStores && dataStoreIdentifier && dataStoreType) {
      dataStores.forEach((ds) => {
        if (
          ds.id === dataStoreIdentifier &&
          ds.type === dataStoreType &&
          ds.location === dataStoreLocation
        ) {
          setDataStore(ds);
        }
      });
    }
    const queryParamString = `per_page=${perPage}&page=${page}&location=${dataStoreLocation}`;
    HttpService.makeCallToBackend({
      path: `/data-stores/${dataStoreType}/${dataStoreIdentifier}/items?${queryParamString}`,
      successCallback: (response: DataStoreRecords) => {
        setResults(response.results);
        setPagination(response.pagination);
      },
    });
  }, [dataStores, searchParams]);

  const getCell = (value: any) => {
    const valueToUse =
      typeof value === 'object' ? (
        <pre>
          <code>{JSON.stringify(value, null, 4)}</code>
        </pre>
      ) : (
        value
      );

    return <TableCell>{valueToUse}</TableCell>;
  };

  const getTable = () => {
    if (results.length === 0) {
      return null;
    }
    const firstResult = results[0];
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
                  return getCell(object[key]);
                })}
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    );
  };

  const locationDescription = (ds: DataStore) => {
    return ds.location ? ` @ ${ds.location}` : '';
  };

  const { page, perPage } = getPageInfoFromSearchParams(
    searchParams,
    10,
    1,
    'datastore',
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
        itemToString={(ds: DataStore) =>
          ds ? `${ds.name} (${ds.type}${locationDescription(ds)})` : ''
        }
        onChange={(event: any) => {
          setDataStore(event.selectedItem);
          searchParams.set('datastore_page', '1');
          searchParams.set('datastore_per_page', '10');
          searchParams.set('type', event.selectedItem.type);
          searchParams.set('identifier', event.selectedItem.id);
          searchParams.set('location', event.selectedItem.location);
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
