import { useEffect, useState } from 'react';
import {
  Table,
  TableHead,
  TableRow,
  TableBody,
  TableCell,
  TableContainer,
  Paper,
  MenuItem,
  Select,
  InputLabel,
  FormControl,
} from '@mui/material';
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
    keys.forEach((key) => tableHeaders.push(<TableCell>{key}</TableCell>));

    return (
      <TableContainer component={Paper}>
        <Table>
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
      </TableContainer>
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
      <FormControl fullWidth>
        <InputLabel id="data-store-dropdown-label">
          Select Data Store
        </InputLabel>
        <Select
          labelId="data-store-dropdown-label"
          label="Select Data Store"
          id="data-store-dropdown"
          value={dataStore ? dataStore.id : ''}
          onChange={(event) => {
            const selectedDataStore = dataStores.find(
              (ds) => ds.id === event.target.value,
            );
            if (selectedDataStore) {
              setDataStore(selectedDataStore);
              searchParams.set('datastore_page', '1');
              searchParams.set('datastore_per_page', '10');
              searchParams.set('type', selectedDataStore.type);
              searchParams.set('identifier', selectedDataStore.id);
              searchParams.set('location', selectedDataStore.location ?? '');
              setSearchParams(searchParams);
            }
          }}
        >
          {dataStores.map((ds) => (
            <MenuItem key={ds.id} value={ds.id}>
              {`${ds.name} (${ds.type}${locationDescription(ds)})`}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
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
