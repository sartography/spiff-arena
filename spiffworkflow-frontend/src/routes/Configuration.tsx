import { useContext, useEffect, useState } from 'react';
import { Route, Routes, useLocation, useNavigate } from 'react-router-dom';
// @ts-ignore
import { Tabs, TabList, Tab } from '@carbon/react';
import { Can } from '@casl/react';
import ErrorContext from '../contexts/ErrorContext';
import SecretList from './SecretList';
import SecretNew from './SecretNew';
import SecretShow from './SecretShow';
import AuthenticationList from './AuthenticationList';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import { PermissionsToCheck } from '../interfaces';
import { usePermissionFetcher } from '../hooks/PermissionService';

export default function Configuration() {
  const location = useLocation();
  const setErrorObject = (useContext as any)(ErrorContext)[1];
  const [selectedTabIndex, setSelectedTabIndex] = useState<number>(0);
  const navigate = useNavigate();

  const { targetUris } = useUriListForPermissions();
  const permissionRequestData: PermissionsToCheck = {
    [targetUris.authenticationListPath]: ['GET'],
    [targetUris.secretListPath]: ['GET'],
  };
  const { ability } = usePermissionFetcher(permissionRequestData);

  useEffect(() => {
    setErrorObject(null);
    let newSelectedTabIndex = 0;
    if (location.pathname.match(/^\/admin\/configuration\/authentications\b/)) {
      newSelectedTabIndex = 1;
    }
    setSelectedTabIndex(newSelectedTabIndex);
  }, [location, setErrorObject]);

  return (
    <>
      <Tabs selectedIndex={selectedTabIndex}>
        <TabList aria-label="List of tabs">
          <Can I="GET" a={targetUris.secretListPath} ability={ability}>
            <Tab onClick={() => navigate('/admin/configuration/secrets')}>
              Secrets
            </Tab>
          </Can>
          <Can I="GET" a={targetUris.authenticationListPath} ability={ability}>
            <Tab
              onClick={() => navigate('/admin/configuration/authentications')}
            >
              Authentications
            </Tab>
          </Can>
        </TabList>
      </Tabs>
      <br />
      <Routes>
        <Route path="/" element={<SecretList />} />
        <Route path="secrets" element={<SecretList />} />
        <Route path="secrets/new" element={<SecretNew />} />
        <Route path="secrets/:key" element={<SecretShow />} />
        <Route path="authentications" element={<AuthenticationList />} />
      </Routes>
    </>
  );
}
