import { useEffect, useState } from 'react';
import { Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { Tabs, Tab } from '@mui/material'; // Use MUI Tabs and Tab
import { Can } from '@casl/react';
import SecretList from './SecretList';
import SecretNew from './SecretNew';
import SecretShow from './SecretShow';
import AuthenticationList from './AuthenticationList';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import { PermissionsToCheck } from '../interfaces';
import { usePermissionFetcher } from '../hooks/PermissionService';
import { setPageTitle } from '../helpers';
import { UiSchemaUxElement } from '../extension_ui_schema_interfaces';
import ExtensionUxElementForDisplay from '../components/ExtensionUxElementForDisplay';
import Extension from './Extension';

type OwnProps = {
  extensionUxElements?: UiSchemaUxElement[] | null;
};

export default function Configuration({ extensionUxElements }: OwnProps) {
  const location = useLocation();
  const [selectedTabIndex, setSelectedTabIndex] = useState<number>(0);
  const navigate = useNavigate();

  const { targetUris } = useUriListForPermissions();
  const permissionRequestData: PermissionsToCheck = {
    [targetUris.authenticationListPath]: ['GET'],
    [targetUris.secretListPath]: ['GET'],
  };
  const { ability, permissionsLoaded } = usePermissionFetcher(
    permissionRequestData,
  );

  useEffect(() => {
    setPageTitle(['Configuration']);
    let newSelectedTabIndex = 0;
    if (
      location.pathname.match(/^\/(newui\/)?configuration\/authentications\b/)
    ) {
      newSelectedTabIndex = 1;
    }
    setSelectedTabIndex(newSelectedTabIndex);
  }, [location]);

  const configurationExtensionTab = (
    uxElement: UiSchemaUxElement,
    uxElementIndex: number,
  ) => {
    const navItemPage = `/configuration/extension${uxElement.page}`;

    let pagesToCheck = [uxElement.page];
    if (
      uxElement.location_specific_configs &&
      uxElement.location_specific_configs.highlight_on_tabs
    ) {
      pagesToCheck = uxElement.location_specific_configs.highlight_on_tabs;
    }

    pagesToCheck.forEach((pageToCheck: string) => {
      const pageToCheckNavItem = `/configuration/extension${pageToCheck}`;
      if (pageToCheckNavItem === location.pathname) {
        setSelectedTabIndex(uxElementIndex + 2);
      }
    });
    return (
      <Tab label={uxElement.label} onClick={() => navigate(navItemPage)} />
    );
  };

  // wow, if you do not check to see if the permissions are loaded, then in safari,
  // you will get {null} inside the <TabList> which totally explodes carbon (in safari!).
  // we *think* that null inside a TabList works fine in all other browsers.
  if (!permissionsLoaded) {
    return null;
  }

  return (
    <>
      <Tabs
        value={selectedTabIndex}
        onChange={(_, newValue) => setSelectedTabIndex(newValue)}
      >
        <Can I="GET" a={targetUris.secretListPath} ability={ability}>
          <Tab
            label="Secrets"
            onClick={() => navigate('/configuration/secrets')}
          />
        </Can>
        <Can I="GET" a={targetUris.authenticationListPath} ability={ability}>
          <Tab
            label="Authentications"
            onClick={() => navigate('/configuration/authentications')}
          />
        </Can>
        <ExtensionUxElementForDisplay
          displayLocation="configuration_tab_item"
          elementCallback={configurationExtensionTab}
          extensionUxElements={extensionUxElements}
        />
      </Tabs>
      <br />
      <Routes>
        <Route path="/" element={<SecretList />} />
        <Route path="secrets" element={<SecretList />} />
        <Route path="secrets/new" element={<SecretNew />} />
        <Route path="secrets/:secret_identifier" element={<SecretShow />} />
        <Route path="authentications" element={<AuthenticationList />} />
        <Route
          path="extension/:page_identifier"
          element={<Extension displayErrors={false} />}
        />
        ;
      </Routes>
    </>
  );
}
