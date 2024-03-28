import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';

import UserService from '../../services/UserService';

export default function SignOut() {
  const logoutUser = () => {
    UserService.doLogout();
  };

  return (
    <div className="fixed-width-container">
      <Typography variant="h1">Access Denied</Typography>
      <Typography variant="body1">
        You are currently logged in as{' '}
        <strong>{UserService.getPreferredUsername()}</strong>. You do not have
        access to this page. Would you like to sign out and sign in as a
        different user?
      </Typography>
      <br />
      <Button
        variant="contained"
        onClick={logoutUser}
        data-qa="public-sign-out"
      >
        Sign out
      </Button>
    </div>
  );
}
