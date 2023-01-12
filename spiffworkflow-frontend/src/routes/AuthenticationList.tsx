import { useContext, useEffect, useState } from 'react';
// @ts-ignore
import { Table } from '@carbon/react';
import ErrorContext from '../contexts/ErrorContext';
import { AuthenticationItem } from '../interfaces';
import HttpService from '../services/HttpService';
import UserService from '../services/UserService';

export default function AuthenticationList() {
  const setErrorObject = (useContext as any)(ErrorContext)[1];

  const [authenticationList, setAuthenticationList] = useState<
    AuthenticationItem[] | null
  >(null);
  const [connectProxyBaseUrl, setConnectProxyBaseUrl] = useState<string | null>(
    null
  );
  const [redirectUrl, setRedirectUrl] = useState<string | null>(null);

  useEffect(() => {
    const processResult = (result: any) => {
      setAuthenticationList(result.results);
      setConnectProxyBaseUrl(result.connector_proxy_base_url);
      setRedirectUrl(result.redirect_url);
    };
    HttpService.makeCallToBackend({
      path: `/authentications`,
      successCallback: processResult,
      failureCallback: setErrorObject,
    });
  }, [setErrorObject]);

  const buildTable = () => {
    if (authenticationList) {
      const rows = authenticationList.map((row) => {
        return (
          <tr key={row.id}>
            <td>
              <a
                data-qa="authentication-create-link"
                href={`${connectProxyBaseUrl}/v1/auth/${
                  row.id
                }?redirect_url=${redirectUrl}/${
                  row.id
                }?token=${UserService.getAccessToken()}`}
              >
                {row.id}
              </a>
            </td>
          </tr>
        );
      });
      return (
        <Table striped bordered>
          <thead>
            <tr>
              <th>Id</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </Table>
      );
    }
    return null;
  };

  if (authenticationList) {
    return <>{buildTable()}</>;
  }

  return <main />;
}
