import { useEffect, useState } from 'react';
import { Button } from '@carbon/react';
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
          size="md"
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
        {authenticationOptionButtons()}
      </div>
    );
  }
  return null;
}
