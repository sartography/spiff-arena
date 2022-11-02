import {
  Header,
  Theme,
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
          <HeaderGlobalAction aria-label="Logout" onClick={handleLogout}>
            <Logout />
          </HeaderGlobalAction>
        </>
      );
    }
    return (
      <HeaderGlobalAction aria-label="Login" onClick={handleLogin}>
        <Login />
      </HeaderGlobalAction>
    );
  };

  if (activeKey) {
    return (
      <div className="spiffworkflow-header-container">
        <Theme theme="g100">
          <Header aria-label="Spiffworkflow">
            <HeaderName href="/" prefix="">
              <img src={logo} className="app-logo" alt="logo" />
            </HeaderName>
            <HeaderNavigation aria-label="Spifffff">
              <HeaderMenuItem href="/" isCurrentPage={isActivePage('/')}>
                Home
              </HeaderMenuItem>
              <HeaderMenuItem
                href="/admin/process-groups"
                isCurrentPage={isActivePage('/admin/process-groups')}
              >
                Processes
              </HeaderMenuItem>
              <HeaderMenuItem
                href="/admin/process-instances"
                isCurrentPage={isActivePage('/admin/process-instances')}
              >
                Process Instances
              </HeaderMenuItem>
            </HeaderNavigation>
            <HeaderGlobalBar>{loginAndLogoutAction()}</HeaderGlobalBar>
          </Header>
        </Theme>
      </div>
    );
  }
  return null;
}
