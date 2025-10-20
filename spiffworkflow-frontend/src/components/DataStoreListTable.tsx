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
import { useSearchParams, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import HttpService from '../services/HttpService';
import { DataStore, DataStoreRecords, PaginationObject } from '../interfaces';
import PaginationForTable from './PaginationForTable';
import { getPageInfoFromSearchParams } from '../helpers';
import DataStoreButtons from './DataStoreButtons';

export default function DataStoreListTable() {
  const [dataStores, setDataStores] = useState<DataStore[]>([]);
  const [dataStore, setDataStore] = useState<DataStore | null>(null);
  const [pagination, setPagination] = useState<PaginationObject | null>(null);
  const [results, setResults] = useState<any[]>([]);
  const [searchParams, setSearchParams] = useSearchParams();
  const location = useLocation();
  const { t } = useTranslation();

  useEffect(() => {
    HttpService.makeCallToBackend({
      path: `/data-stores`,
      successCallback: (newStores: DataStore[]) => {
        setDataStores(newStores);
      },
    });
  }, [location.key]); // Refresh data stores list on any navigation (including back from deletion)

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
      // Clear state when no data store is selected (e.g., after deletion and navigation back to /data-stores)
      setDataStore(null);
      setResults([]);
      setPagination(null);
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

  const getFullDataStoreId = (ds: DataStore) => {
    const locationPrefix = ds.location ? `${ds.location}/` : '';
    return `${ds.type}:${locationPrefix}${ds.id}`;
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
          {t('select_data_store')}
        </InputLabel>
        <Select
          labelId="data-store-dropdown-label"
          label={t('select_data_store')}
          id="data-store-dropdown"
          value={dataStore ? getFullDataStoreId(dataStore) : ''}
          onChange={(event) => {
            const selectedDataStore = dataStores.find(
              (ds) => getFullDataStoreId(ds) === event.target.value,
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
            <MenuItem
              key={getFullDataStoreId(ds)}
              value={getFullDataStoreId(ds)}
            >
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
      {dataStore && <DataStoreButtons dataStore={dataStore} />}
    </>
  );
}
