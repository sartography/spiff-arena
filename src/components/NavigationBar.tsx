import { Button, Navbar, Nav, Container } from 'react-bootstrap';
// @ts-expect-error TS(2307) FIXME: Cannot find module '../logo.svg' or its correspond... Remove this comment to see the full error message
import logo from '../logo.svg';
import UserService from '../services/UserService';

// for ref: https://react-bootstrap.github.io/components/navbar/
export default function NavigationBar() {
  const navElements = null;

  const handleLogout = () => {
    UserService.doLogout();
  };

  const handleLogin = () => {
    UserService.doLogin();
  };

  const loginLink = () => {
    if (!UserService.isLoggedIn()) {
      return (
        <Navbar.Collapse className="justify-content-end">
          <Navbar.Text>
            <Button variant="link" onClick={handleLogin}>
              Login
            </Button>
          </Navbar.Text>
        </Navbar.Collapse>
      );
    }
    return null;
  };

  const logoutLink = () => {
    if (UserService.isLoggedIn()) {
      return (
        <Navbar.Collapse className="justify-content-end">
          <Navbar.Text>
            Signed in as: <strong>{UserService.getUsername()}</strong>
          </Navbar.Text>
          <Navbar.Text>
            <Button
              variant="link"
              onClick={handleLogout}
              data-qa="logout-button"
            >
              Logout
            </Button>
          </Navbar.Text>
        </Navbar.Collapse>
      );
    }
    return null;
  };

  return (
    <Navbar bg="dark" expand="lg" variant="dark">
      <Container>
        <Navbar.Brand data-qa="spiffworkflow-logo" href="/admin">
          <img src={logo} className="app-logo" alt="logo" />
        </Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="me-auto">{navElements}</Nav>
        </Navbar.Collapse>
        {loginLink()}
        {logoutLink()}
      </Container>
    </Navbar>
  );
}
