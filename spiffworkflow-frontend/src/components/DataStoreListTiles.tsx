import { ReactElement, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { ArrowRight } from '@carbon/icons-react';
import { ClickableTile } from '@carbon/react';
import HttpService from '../services/HttpService';
import { DataStore } from '../interfaces';
import {
  modifyProcessIdentifierForPathParam,
  truncateString,
} from '../helpers';

type OwnProps = {
  defaultDataStores?: DataStore[];
  dataStore?: DataStore;
  headerElement?: ReactElement;
  showNoItemsDisplayText?: boolean;
  userCanCreateDataStores?: boolean;
};

export default function DataStoreListTiles({
  defaultDataStores,
  dataStore,
  headerElement,
  showNoItemsDisplayText,
  userCanCreateDataStores,
}: OwnProps) {
  const [searchParams] = useSearchParams();

  const [dataStores, setDataStores] = useState<DataStore[] | null>(
    null
  );

  useEffect(() => {
    const setDataStoresFromResult = (result: any) => {
      setDataStores(result);
      console.log(result);
      console.log(dataStores);
    };

    if (defaultDataStores) {
      setDataStores(defaultDataStores);
    } else {
    /*
      let queryParams = '?per_page=1000';
      if (processGroup) {
        queryParams = `${queryParams}&process_group_identifier=${processGroup.id}`;
      }
      */
      let queryParams = '';
      HttpService.makeCallToBackend({
        path: `/data-stores${queryParams}`,
        successCallback: setDataStoresFromResult,
      });
    }
  }, [searchParams, dataStore, defaultDataStores]);

  const dataStoresDisplayArea = () => {
    let displayText = null;
    if (dataStores && dataStores.length > 0) {
      displayText = dataStores.map((row: DataStore) => {
        return (
          <ClickableTile
            id={`data-store-tile-${row.id}`}
            className="tile-data-store"
            href={`/data-stores/${
              row.id
            }`}
          >
            <div className="tile-data-store-content-container">
              <ArrowRight />
              <div className="tile-data-store-display-name">
                {row.name}
              </div>
              <p className="tile-description">
                {truncateString(row.description || '', 100)}
              </p>
            </div>
          </ClickableTile>
        );
      });
    } else if (userCanCreateDataStores) {
      displayText = (
        <p className="no-results-message">
          There are no data stores to display. You can add one by clicking
          the &quot;Add a data store&quot; button.
        </p>
      );
    } else {
      displayText = (
        <p className="no-results-message">
          There are no data stores to display.
        </p>
      );
    }
    return displayText;
  };

  const dataStoreArea = () => {
    if (dataStores && (showNoItemsDisplayText || dataStores.length > 0)) {
      return (
        <>
          {headerElement}
          {dataStoresDisplayArea()}
        </>
      );
    }
    return null;
  };

  if (dataStores) {
    return (
      <>
        {/* so we can check if the data stores have loaded in cypress tests */}
        <div data-qa="data-stores-loaded" className="hidden" />
        {dataStoreArea()}
      </>
    );
  }
  return null;
}
