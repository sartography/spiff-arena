import { ReactElement, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { ArrowRight } from '@carbon/icons-react';
import { ClickableTile } from '@carbon/react';
import HttpService from '../services/HttpService';
import { DataStore, PermissionsToCheck, ProcessGroup } from '../interfaces';
import { truncateString } from '../helpers';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import { usePermissionFetcher } from '../hooks/PermissionService';

type OwnProps = {
  defaultDataStores?: DataStore[];
  dataStore?: DataStore;
  processGroup?: ProcessGroup;
  headerElement?: ReactElement;
  showNoItemsDisplayText?: boolean;
  userCanCreateDataStores?: boolean;
};

export default function DataStoreListTiles({
  defaultDataStores,
  dataStore,
  processGroup,
  headerElement,
  showNoItemsDisplayText,
  userCanCreateDataStores,
}: OwnProps) {
  const [searchParams] = useSearchParams();

  const [dataStores, setDataStores] = useState<DataStore[] | null>(null);
  const { targetUris } = useUriListForPermissions();
  const permissionRequestData: PermissionsToCheck = {
    [targetUris.dataStoreListPath]: ['GET'],
  };
  const { ability, permissionsLoaded } = usePermissionFetcher(
    permissionRequestData,
  );

  useEffect(() => {
    if (permissionsLoaded && ability.can('GET', targetUris.dataStoreListPath)) {
      if (defaultDataStores) {
        setDataStores(defaultDataStores);
      } else {
        const queryParams = `?per_page=1000&process_group_identifier=${
          processGroup?.id ?? ''
        }`;
        HttpService.makeCallToBackend({
          path: `${targetUris.dataStoreListPath}${queryParams}`,
          successCallback: setDataStores,
        });
      }
    }
  }, [
    searchParams,
    dataStore,
    defaultDataStores,
    processGroup,
    permissionsLoaded,
    ability,
    targetUris.dataStoreListPath,
  ]);

  const dataStoresDisplayArea = () => {
    let displayText = null;
    if (dataStores && dataStores.length > 0) {
      displayText = dataStores.map((row: DataStore) => {
        return (
          <ClickableTile
            id={`data-store-tile-${row.id}`}
            className="tile-data-store"
            href={`/data-stores/${row.id}/edit?type=${row.type}&parentGroupId=${
              processGroup?.id ?? ''
            }`}
          >
            <div className="tile-data-store-content-container">
              <ArrowRight />
              <div className="tile-data-store-display-name">{row.name}</div>
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
          There are no data stores to display. You can add one by clicking the
          &quot;Add a data store&quot; button.
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
