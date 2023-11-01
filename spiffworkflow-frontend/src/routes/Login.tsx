import { ArrowRight } from '@carbon/icons-react';
import { useEffect, useState } from 'react';
import { Button, Grid, Column } from '@carbon/react';
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
    if (authenticationOptions.length === 1) {
      UserService.doLogin(
        authenticationOptions[0],
        searchParams.get('original_url')
      );
      return null;
    }
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

  if (authenticationOptions !== null) {
    return (
      <div className="fixed-width-container">
        <Grid>
          <Column
            lg={{ span: 5, offset: 6 }}
            md={{ span: 4, offset: 2 }}
            sm={{ span: 4, offset: 0 }}
          >
            <h1 className="with-large-bottom-margin with-top-margin">
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
  }
  return null;
}
