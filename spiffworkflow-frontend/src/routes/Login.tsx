import { ArrowRight } from '@carbon/icons-react';
import { useEffect, useState } from 'react';
import { Loading, Button, Grid, Column } from '@carbon/react';
import { useSearchParams } from 'react-router-dom';
import { AuthenticationOption } from '../interfaces';
import HttpService from '../services/HttpService';
import UserService from '../services/UserService';

export default function Login() {
  const [searchParams] = useSearchParams();
  const [authenticationOptions, setAuthenticationOptions] = useState<
    AuthenticationOption[] | null
  >(null);
  useEffect(() => {
    HttpService.makeCallToBackend({
      path: '/authentication-options',
      successCallback: setAuthenticationOptions,
    });
  }, []);

  const authenticationOptionButtons = () => {
    if (!authenticationOptions) {
      return null;
    }
    const buttons: any = [];
    authenticationOptions.forEach((option: AuthenticationOption) => {
      buttons.push(
        <Button
          data-qa={`login-button-${option.identifier}`}
          size="lg"
          className="login-button"
          renderIcon={ArrowRight}
          onClick={() =>
            UserService.doLogin(option, searchParams.get('original_url'))
          }
        >
          {option.label}
        </Button>
      );
    });
    return buttons;
  };

  const doLoginIfAppropriate = () => {
    if (!authenticationOptions) {
      return;
    }
    if (authenticationOptions.length === 1) {
      UserService.doLogin(
        authenticationOptions[0],
        searchParams.get('original_url')
      );
    }
  };

  const getLoadingIcon = () => {
    const style = { margin: '50px 0 50px 50px' };
    return (
      <Loading
        description="Active loading indicator"
        withOverlay={false}
        style={style}
      />
    );
  };

  const loginComponments = () => {
    return (
      <div className="fixed-width-container login-page-spacer">
        <Grid>
          <Column
            lg={{ span: 5, offset: 6 }}
            md={{ span: 4, offset: 2 }}
            sm={{ span: 4, offset: 0 }}
          >
            <h1 className="with-large-bottom-margin">
              Log in to SpiffWorkflow
            </h1>
          </Column>
          <Column
            lg={{ span: 8, offset: 5 }}
            md={{ span: 5, offset: 2 }}
            sm={{ span: 4, offset: 0 }}
          >
            {authenticationOptionButtons()}
          </Column>
        </Grid>
      </div>
    );
  };

  if (authenticationOptions === null || authenticationOptions.length < 2) {
    doLoginIfAppropriate();
    return (
      <div className="fixed-width-container login-page-spacer">
        {getLoadingIcon()}
      </div>
    );
  }

  if (authenticationOptions !== null) {
    doLoginIfAppropriate();
    return loginComponments();
  }

  return null;
}
