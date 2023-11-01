import { useEffect, useState } from 'react';
import { Button } from '@carbon/react';
import { useSearchParams } from 'react-router-dom';
import { AuthenticationOption } from '../interfaces';
import HttpService from '../services/HttpService';
import UserService from '../services/UserService';

export default function Login() {
  // TODO: if only one auth option then go there initially instead of getting the list

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
    return authenticationOptionButtons();
  }
  return null;
}
