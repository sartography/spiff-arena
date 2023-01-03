import {
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
  // @ts-ignore
} from '@carbon/react';
// @ts-ignore
import { Logout, Login } from '@carbon/icons-react';
import { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { Can } from '@casl/react';
// @ts-expect-error TS(2307) FIXME: Cannot find module '../logo.svg' or its correspond... Remove this comment to see the full error message
import logo from '../logo.svg';
import UserService from '../services/UserService';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import { PermissionsToCheck } from '../interfaces';
import { usePermissionFetcher } from '../hooks/PermissionService';
import { UnauthenticatedError } from '../services/HttpService';

// for ref: https://react-bootstrap.github.io/components/navbar/
export default function NavigationBar() {
  const handleLogout = () => {
    UserService.doLogout();
  };

  const handleLogin = () => {
    UserService.doLogin();
  };

  const location = useLocation();
  const [activeKey, setActiveKey] = useState<string>('');

  const { targetUris } = useUriListForPermissions();

  // App.jsx forces login (which redirects to keycloak) so we should never get here if we're not logged in.
  if (!UserService.isLoggedIn()) {
    throw new UnauthenticatedError('You must be authenticated to do this.');
  }
  const permissionRequestData: PermissionsToCheck = {
    [targetUris.authenticationListPath]: ['GET'],
    [targetUris.messageInstanceListPath]: ['GET'],
    [targetUris.secretListPath]: ['GET'],
  };
  const { ability } = usePermissionFetcher(permissionRequestData);

  useEffect(() => {
    let newActiveKey = '/admin/process-groups';
    if (location.pathname.match(/^\/admin\/messages\b/)) {
      newActiveKey = '/admin/messages';
    } else if (
      location.pathname.match(/^\/admin\/process-instances\/reports\b/)
    ) {
      newActiveKey = '/admin/process-instances/reports';
    } else if (location.pathname.match(/^\/admin\/process-instances\b/)) {
      newActiveKey = '/admin/process-instances';
    } else if (location.pathname.match(/^\/admin\/configuration\b/)) {
      newActiveKey = '/admin/configuration';
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

  const loginAndLogoutAction = () => {
    if (UserService.isLoggedIn()) {
      return (
        <>
          <HeaderGlobalAction className="username-header-text">
            {UserService.getPreferredUsername()}
          </HeaderGlobalAction>
          <HeaderGlobalAction
            aria-label="Logout"
            onClick={handleLogout}
            data-qa="logout-button"
          >
            <Logout />
          </HeaderGlobalAction>
        </>
      );
    }
    return (
      <HeaderGlobalAction
        data-qa="login-button"
        aria-label="Login"
        onClick={handleLogin}
      >
        <Login />
      </HeaderGlobalAction>
    );
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
                      href="/admin/configuration"
                      isCurrentPage={isActivePage('/admin/configuration')}
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

  const headerMenuItems = () => {
    if (!UserService.isLoggedIn()) {
      return null;
    }
    return (
      <>
        <HeaderMenuItem href="/" isCurrentPage={isActivePage('/')}>
          Home
        </HeaderMenuItem>
        <HeaderMenuItem
          href="/admin/process-groups"
          isCurrentPage={isActivePage('/admin/process-groups')}
          data-qa="header-nav-processes"
        >
          Processes
        </HeaderMenuItem>
        <HeaderMenuItem
          href="/admin/process-instances"
          isCurrentPage={isActivePage('/admin/process-instances')}
        >
          Process Instances
        </HeaderMenuItem>
        <Can I="GET" a={targetUris.messageInstanceListPath} ability={ability}>
          <HeaderMenuItem
            href="/admin/messages"
            isCurrentPage={isActivePage('/admin/messages')}
          >
            Messages
          </HeaderMenuItem>
        </Can>
        {configurationElement()}
        <HeaderMenuItem
          hidden
          href="/admin/process-instances/reports"
          isCurrentPage={isActivePage('/admin/process-instances/reports')}
        >
          Perspectives
        </HeaderMenuItem>
      </>
    );
  };

  if (activeKey && ability) {
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
            <HeaderGlobalBar>{loginAndLogoutAction()}</HeaderGlobalBar>
          </Header>
        )}
      />
    );
  }
  return null;
}
