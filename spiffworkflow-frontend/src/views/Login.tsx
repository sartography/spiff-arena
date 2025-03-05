import { ArrowForward } from '@mui/icons-material';
import { useCallback, useEffect, useState } from 'react';
import { CircularProgress, Button, Grid, Typography } from '@mui/material';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { AuthenticationOption } from '../interfaces';
import HttpService from '../services/HttpService';
import UserService from '../services/UserService';

export default function Login() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [authenticationOptions, setAuthenticationOptions] = useState<
    AuthenticationOption[] | null
  >(null);

  const originalUrl = searchParams.get('original_url');
  const getOriginalUrl = useCallback(() => {
    if (originalUrl === '/login') {
      return '/';
    }
    return originalUrl;
  }, [originalUrl]);

  useEffect(() => {
    HttpService.makeCallToBackend({
      path: '/authentication-options',
      successCallback: setAuthenticationOptions,
    });
  }, [getOriginalUrl]);

  const authenticationOptionButtons = () => {
    if (!authenticationOptions) {
      return null;
    }
    const buttons: any = [];
    authenticationOptions.forEach((option: AuthenticationOption) => {
      buttons.push(
        <Button
          key={option.identifier}
          data-qa={`login-button-${option.identifier}`}
          size="large"
          variant="contained"
          endIcon={<ArrowForward />}
          onClick={() => UserService.doLogin(option, getOriginalUrl())}
          style={{ margin: '10px' }}
        >
          {option.label}
        </Button>,
      );
    });
    return buttons;
  };

  const getLoadingIcon = () => {
    const style = { margin: '50px 0 50px 50px' };
    return <CircularProgress style={style} />;
  };

  const loginComponents = () => {
    return (
      <div className="fixed-width-container login-page-spacer">
        <Grid container spacing={3}>
          <Grid item lg={5} md={4} sm={4}>
            <Typography variant="h4" className="with-large-bottom-margin">
              Log in to SpiffWorkflow
            </Typography>
          </Grid>
          <Grid item lg={8} md={5} sm={4}>
            {authenticationOptionButtons()}
          </Grid>
        </Grid>
      </div>
    );
  };

  if (UserService.isLoggedIn()) {
    navigate('/');
    return null;
  }

  if (authenticationOptions === null) {
    return (
      <div className="fixed-width-container login-page-spacer">
        {getLoadingIcon()}
      </div>
    );
  }

  if (authenticationOptions !== null) {
    if (authenticationOptions.length === 1) {
      UserService.doLogin(authenticationOptions[0], getOriginalUrl());
      return null;
    }
    return loginComponents();
  }

  return null;
}
