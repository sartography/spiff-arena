import {
  Header,
  Theme,
  HeaderName,
  HeaderContainer,
  HeaderNavigation,
  HeaderMenuItem,
  HeaderMenu,
  // @ts-ignore
} from '@carbon/react';
import { useEffect, useState } from 'react';
import { Navbar, Nav } from 'react-bootstrap';
import { useLocation } from 'react-router-dom';
// @ts-expect-error TS(2307) FIXME: Cannot find module '../logo.svg' or its correspond... Remove this comment to see the full error message
import logo from '../logo.svg';
import UserService from '../services/UserService';

// for ref: https://react-bootstrap.github.io/components/navbar/
export default function NavigationBar() {
  // const navElements = null;
  //
  // const handleLogout = () => {
  //   UserService.doLogout();
  // };
  //
  // const handleLogin = () => {
  //   UserService.doLogin();
  // };
  //
  // const loginLink = () => {
  //   if (!UserService.isLoggedIn()) {
  //     return (
  //       <Navbar.Collapse className="justify-content-end">
  //         <Navbar.Text>
  //           <Button variant="link" onClick={handleLogin}>
  //             Login
  //           </Button>
  //         </Navbar.Text>
  //       </Navbar.Collapse>
  //     );
  //   }
  //   return null;
  // };
  //
  // const logoutLink = () => {
  //   if (UserService.isLoggedIn()) {
  //     return (
  //       <Navbar.Collapse className="justify-content-end">
  //         <Navbar.Text>
  //           Signed in as: <strong>{UserService.getUsername()}</strong>
  //         </Navbar.Text>
  //         <Navbar.Text>
  //           <Button
  //             variant="link"
  //             onClick={handleLogout}
  //             data-qa="logout-button"
  //           >
  //             Logout
  //           </Button>
  //         </Navbar.Text>
  //       </Navbar.Collapse>
  //     );
  //   }
  //   return null;
  // };

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

  //   return (
  // <Theme theme="g100">
  //     <Navbar bg="dark" expand="lg" variant="dark">
  //       <Content>
  //         <Navbar.Brand data-qa="spiffworkflow-logo" href="/admin">
  //           <img src={logo} className="app-logo" alt="logo" />
  //         </Navbar.Brand>
  //         <Navbar.Toggle aria-controls="basic-navbar-nav" />
  //         <Navbar.Collapse id="basic-navbar-nav">
  //           <Nav className="me-auto">{navElements}</Nav>
  //         </Navbar.Collapse>
  //         {loginLink()}
  //         {logoutLink()}
  //       </Content>
  //     </Navbar>
  //     </Theme>
  //   );

  // <Theme theme="g100">
  //   <Header aria-label="IBM Platform Name">
  //     <HeaderName href="#" prefix="IBM">
  //       [Platform]
  //     </HeaderName>
  //     <HeaderNavigation aria-label="IBM [Platform]">
  //       <HeaderMenuItem href="#">Link 1</HeaderMenuItem>
  //       <HeaderMenuItem href="#">Link 2</HeaderMenuItem>
  //       <HeaderMenuItem href="#">Link 3</HeaderMenuItem>
  //       <HeaderMenu aria-label="Link 4" menuLinkName="Link 4">
  //         <HeaderMenuItem href="#">Sub-link 1</HeaderMenuItem>
  //         <HeaderMenuItem href="#">Sub-link 2</HeaderMenuItem>
  //         <HeaderMenuItem href="#">Sub-link 3</HeaderMenuItem>
  //       </HeaderMenu>
  //     </HeaderNavigation>
  //   </Header>
  // </Theme>
  if (activeKey) {
    return (
      <HeaderContainer>
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
          </Header>
        </Theme>
      </HeaderContainer>
    );
  }
  return null;
}
