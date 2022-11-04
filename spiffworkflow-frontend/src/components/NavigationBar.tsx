import {
  Header,
  HeaderContainer,
  HeaderMenuButton,
  SkipToContent,
  Theme,
  HeaderMenu,
  SideNav,
  SideNavItem,
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
// @ts-expect-error TS(2307) FIXME: Cannot find module '../logo.svg' or its correspond... Remove this comment to see the full error message
import logo from '../logo.svg';
import UserService from '../services/UserService';

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

  useEffect(() => {
    let newActiveKey = '/admin/process-groups';
    if (location.pathname.match(/^\/admin\/messages\b/)) {
      newActiveKey = '/admin/messages';
    } else if (location.pathname.match(/^\/admin\/process-instances\b/)) {
      newActiveKey = '/admin/process-instances';
    } else if (location.pathname.match(/^\/admin\/secrets\b/)) {
      newActiveKey = '/admin/secrets';
    } else if (location.pathname.match(/^\/admin\/authentications\b/)) {
      newActiveKey = '/admin/authentications';
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
          <HeaderGlobalAction>{UserService.getUsername()}</HeaderGlobalAction>
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

  const headerMenuItems = () => {
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
      </>
    );
  };

  if (activeKey) {
    // TODO: apply theme g100 to the header
    return (
      <HeaderContainer
        render={({ isSideNavExpanded, onClickSideNavExpand }: any) => (
          <Header aria-label="IBM Platform Name">
            <SkipToContent />
            <HeaderMenuButton
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
