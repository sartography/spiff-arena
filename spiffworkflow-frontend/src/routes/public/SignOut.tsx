import Button from '@mui/material/Button';
import UserService from '../../services/UserService';

export default function SignOut() {
  const logoutUser = () => {
    UserService.doLogout();
  };

  return (
    <>
      <h1>Access Denied</h1>
      <p>
        You are currently logged in as{' '}
        <strong>{UserService.getPreferredUsername()}</strong>. You do not have
        access to this page. Would you like to sign out and sign in as a
        different user?
      </p>
      <br />
      <Button variant="contained" onClick={logoutUser}>
        Sign out
      </Button>
    </>
  );
}
