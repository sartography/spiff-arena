import { useEffect, useState } from 'react';
import { Route, Routes, useLocation, useNavigate } from 'react-router-dom';
// @ts-ignore
import { Tabs, TabList, Tab } from '@carbon/react';
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
    if (location.pathname.match(/^\/configuration\/authentications\b/)) {
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
    return <Tab onClick={() => navigate(navItemPage)}>{uxElement.label}</Tab>;
  };

  // wow, if you do not check to see if the permissions are loaded, then in safari,
  // you will get {null} inside the <TabList> which totally explodes carbon (in safari!).
  // we *think* that null inside a TabList works fine in all other browsers.
  if (!permissionsLoaded) {
    return null;
  }

  return (
    <>
      <Tabs selectedIndex={selectedTabIndex}>
        <TabList aria-label="List of tabs">
          <Can I="GET" a={targetUris.secretListPath} ability={ability}>
            <Tab onClick={() => navigate('/configuration/secrets')}>
              Secrets
            </Tab>
          </Can>
          <Can I="GET" a={targetUris.authenticationListPath} ability={ability}>
            <Tab onClick={() => navigate('/configuration/authentications')}>
              Authentications
            </Tab>
          </Can>
          <ExtensionUxElementForDisplay
            displayLocation="configuration_tab_item"
            elementCallback={configurationExtensionTab}
            extensionUxElements={extensionUxElements}
          />
        </TabList>
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
