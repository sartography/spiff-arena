import {
  Toggletip,
  ToggletipButton,
  ToggletipContent,
  Button,
  Header,
  HeaderContainer,
  HeaderMenuButton,
  SkipToContent,
  SideNav,
  SideNavItems,
  HeaderSideNavItems,
  HeaderName,
  HeaderNavigation,
  HeaderMenuItem,
  HeaderGlobalAction,
  HeaderGlobalBar,
} from '@carbon/react';
import { Logout } from '@carbon/icons-react';
import { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { Can } from '@casl/react';
// @ts-expect-error TS(2307) FIXME: Cannot find module '../logo.svg' or its correspond... Remove this comment to see the full error message
import logo from '../logo.svg';
import UserService from '../services/UserService';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import { PermissionsToCheck } from '../interfaces';
import { UiSchemaUxElement } from '../extension_ui_schema_interfaces';
import { usePermissionFetcher } from '../hooks/PermissionService';
import { DOCUMENTATION_URL, SPIFF_ENVIRONMENT } from '../config';
import appVersionInfo from '../helpers/appVersionInfo';
import { slugifyString } from '../helpers';
import ExtensionUxElementForDisplay from './ExtensionUxElementForDisplay';

type OwnProps = {
  extensionUxElements?: UiSchemaUxElement[] | null;
};

export default function NavigationBar({ extensionUxElements }: OwnProps) {
  const handleLogout = () => {
    UserService.doLogout();
  };

  const location = useLocation();
  const [activeKey, setActiveKey] = useState<string>('');

  const { targetUris } = useUriListForPermissions();
  const permissionRequestData: PermissionsToCheck = {
    [targetUris.authenticationListPath]: ['GET'],
    [targetUris.messageInstanceListPath]: ['GET'],
    [targetUris.secretListPath]: ['GET'],
    [targetUris.dataStoreListPath]: ['GET'],
    [targetUris.extensionListPath]: ['GET'],
    [targetUris.processInstanceListForMePath]: ['POST'],
    [targetUris.processGroupListPath]: ['GET'],
  };
  const { ability } = usePermissionFetcher(permissionRequestData);

  // default to readthedocs and let someone specify an environment variable to override:
  //
  let documentationUrl = 'https://spiffworkflow.readthedocs.io';
  if (DOCUMENTATION_URL) {
    documentationUrl = DOCUMENTATION_URL;
  }

  const processGroupPath = '/process-groups';

  const versionInfo = appVersionInfo();

  useEffect(() => {
    let newActiveKey = 'unknown';
    if (location.pathname.match(/^\/messages\b/)) {
      newActiveKey = '/messages';
    } else if (location.pathname.match(/^\/process-instances\/reports\b/)) {
      newActiveKey = '/process-instances/reports';
    } else if (location.pathname.match(/^\/process-instances\b/)) {
      newActiveKey = '/process-instances';
    } else if (location.pathname.match(/^\/process-(groups|models)\b/)) {
      newActiveKey = processGroupPath;
    } else if (location.pathname.match(/^\/editor\b/)) {
      newActiveKey = processGroupPath;
    } else if (location.pathname.match(/^\/configuration\b/)) {
      newActiveKey = '/configuration';
    } else if (location.pathname.match(/^\/data-stores\b/)) {
      newActiveKey = '/data-stores';
    } else if (location.pathname === '/') {
      newActiveKey = '/';
    } else if (location.pathname.match(/^\/tasks\b/)) {
      newActiveKey = '/';
    }
    setActiveKey(newActiveKey);
  }, [location]);

  const isActivePage = (menuItemPath: string) => {
    return activeKey === menuItemPath;
  };

  const userEmail = UserService.getUserEmail();
  const username = UserService.getPreferredUsername();

  const extensionUserProfileElement = (uxElement: UiSchemaUxElement) => {
    const navItemPage = `/extensions${uxElement.page}`;
    return <a href={navItemPage}>{uxElement.label}</a>;
  };

  const profileToggletip = () => {
    let aboutLinkElement = null;

    if (Object.keys(versionInfo).length) {
      aboutLinkElement = <a href="/about">About</a>;
    }

    return (
      <div style={{ display: 'flex' }} id="user-profile-toggletip">
        <Toggletip isTabTip align="bottom-right">
          <ToggletipButton
            aria-label="User Actions"
            className="user-profile-toggletip-button"
            type="button"
          >
            <div className="user-circle">{username[0].toUpperCase()}</div>
          </ToggletipButton>
          <ToggletipContent className="user-profile-toggletip-content">
            <p>
              <strong>{username}</strong>
            </p>
            {username !== userEmail && <p>{userEmail}</p>}
            <hr />
            {aboutLinkElement}
            <a target="_blank" href={documentationUrl} rel="noreferrer">
              Documentation
            </a>
            <ExtensionUxElementForDisplay
              displayLocation="user_profile_item"
              elementCallback={extensionUserProfileElement}
              extensionUxElements={extensionUxElements}
            />
            {!UserService.authenticationDisabled() ? (
              <>
                <hr />
                <Button
                  data-qa="logout-button"
                  className="button-link"
                  onClick={handleLogout}
                >
                  <Logout />
                  &nbsp;&nbsp;Sign out
                </Button>
              </>
            ) : null}
          </ToggletipContent>
        </Toggletip>
      </div>
    );
  };

  const logoutAction = () => {
    if (UserService.isLoggedIn()) {
      return (
        <>
          {SPIFF_ENVIRONMENT ? (
            <HeaderGlobalAction
              title={`The current SpiffWorkflow environment is: ${SPIFF_ENVIRONMENT}`}
              className="spiff-environment-header-text unclickable-text"
            >
              {SPIFF_ENVIRONMENT}
            </HeaderGlobalAction>
          ) : null}
          {profileToggletip()}
        </>
      );
    }
    return null;
  };

  const configurationElement = () => {
    return (
      <Can
        I="GET"
        a={targetUris.authenticationListPath}
        ability={ability}
        passThrough
      >
        {(authenticationAllowed: boolean) => {
          return (
            <Can
              I="GET"
              a={targetUris.secretListPath}
              ability={ability}
              passThrough
            >
              {(secretAllowed: boolean) => {
                if (secretAllowed || authenticationAllowed) {
                  return (
                    <HeaderMenuItem
                      href="/configuration"
                      isCurrentPage={isActivePage('/configuration')}
                    >
                      Configuration
                    </HeaderMenuItem>
                  );
                }
                return null;
              }}
            </Can>
          );
        }}
      </Can>
    );
  };

  const extensionHeaderMenuItemElement = (uxElement: UiSchemaUxElement) => {
    const navItemPage = `/extensions${uxElement.page}`;
    const regexp = new RegExp(`^${navItemPage}$`);
    if (regexp.test(location.pathname)) {
      setActiveKey(navItemPage);
    }
    return (
      <HeaderMenuItem
        href={navItemPage}
        isCurrentPage={isActivePage(navItemPage)}
        data-qa={`extension-${slugifyString(uxElement.label)}`}
      >
        {uxElement.label}
      </HeaderMenuItem>
    );
  };

  const headerMenuItems = () => {
    if (!UserService.isLoggedIn()) {
      return null;
    }
    return (
      <>
        <HeaderMenuItem href="/" isCurrentPage={isActivePage('/')}>
          Home
        </HeaderMenuItem>
        <Can I="GET" a={targetUris.processGroupListPath} ability={ability}>
          <HeaderMenuItem
            href={processGroupPath}
            isCurrentPage={isActivePage(processGroupPath)}
            data-qa="header-nav-processes"
          >
            Processes
          </HeaderMenuItem>
        </Can>
        <Can
          I="POST"
          a={targetUris.processInstanceListForMePath}
          ability={ability}
        >
          <HeaderMenuItem
            href="/process-instances"
            isCurrentPage={isActivePage('/process-instances')}
          >
            Process Instances
          </HeaderMenuItem>
        </Can>
        <Can I="GET" a={targetUris.messageInstanceListPath} ability={ability}>
          <HeaderMenuItem
            href="/messages"
            isCurrentPage={isActivePage('/messages')}
          >
            Messages
          </HeaderMenuItem>
        </Can>
        <Can I="GET" a={targetUris.dataStoreListPath} ability={ability}>
          <HeaderMenuItem
            href="/data-stores"
            isCurrentPage={isActivePage('/data-stores')}
          >
            Data Stores
          </HeaderMenuItem>
        </Can>
        {configurationElement()}
        <ExtensionUxElementForDisplay
          displayLocation="header_menu_item"
          elementCallback={extensionHeaderMenuItemElement}
          extensionUxElements={extensionUxElements}
        />
      </>
    );
  };

  // App.jsx forces login (which redirects to keycloak) so we should never get here if we're not logged in.
  if (!UserService.isLoggedIn()) {
    return (
      <HeaderContainer
        render={() => (
          <Header aria-label="IBM Platform Name" className="cds--g100">
            <HeaderName href="/" prefix="" data-qa="spiffworkflow-logo">
              <img src={logo} className="app-logo" alt="logo" />
            </HeaderName>
          </Header>
        )}
      />
    );
  }

  if (activeKey && ability && !UserService.onlyGuestTaskCompletion()) {
    return (
      <HeaderContainer
        render={({ isSideNavExpanded, onClickSideNavExpand }: any) => (
          <Header aria-label="IBM Platform Name" className="cds--g100">
            <SkipToContent />
            <HeaderMenuButton
              data-qa="header-menu-expand-button"
              aria-label="Open menu"
              onClick={onClickSideNavExpand}
              isActive={isSideNavExpanded}
            />
            <HeaderName href="/" prefix="" data-qa="spiffworkflow-logo">
              <img src={logo} className="app-logo" alt="logo" />
            </HeaderName>
            <HeaderNavigation
              data-qa="main-nav-header"
              aria-label="Spiffworkflow"
            >
              {headerMenuItems()}
            </HeaderNavigation>
            <SideNav
              data-qa="side-nav-items"
              aria-label="Side navigation"
              expanded={isSideNavExpanded}
              isPersistent={false}
            >
              <SideNavItems>
                <HeaderSideNavItems>{headerMenuItems()}</HeaderSideNavItems>
              </SideNavItems>
            </SideNav>
            <HeaderGlobalBar>{logoutAction()}</HeaderGlobalBar>
          </Header>
        )}
      />
    );
  }
  return null;
}
