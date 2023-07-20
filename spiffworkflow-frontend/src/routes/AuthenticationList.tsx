import { useEffect, useState } from 'react';
// @ts-ignore
import { Table } from '@carbon/react';
import { AuthenticationItem } from '../interfaces';
import HttpService from '../services/HttpService';
import UserService from '../services/UserService';

export default function AuthenticationList() {
  const [authenticationList, setAuthenticationList] = useState<
    AuthenticationItem[] | null
  >(null);
  const [authenticationV2List, setAuthenticationV2List] = useState<
    AuthenticationItem[] | null
  >(null);
  const [connectProxyBaseUrl, setConnectProxyBaseUrl] = useState<string | null>(
    null
  );
  const [redirectUrl, setRedirectUrl] = useState<string | null>(null);

  useEffect(() => {
    const processResult = (result: any) => {
      setAuthenticationList(result.results);
      setAuthenticationV2List(result.resultsV2);
      setConnectProxyBaseUrl(result.connector_proxy_base_url);
      setRedirectUrl(result.redirect_url);
    };
    HttpService.makeCallToBackend({
      path: `/authentications`,
      successCallback: processResult,
    });
  }, []);

  const buildTable = () => {
    if (authenticationList && authenticationV2List) {
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
      const rowsV2 = authenticationV2List.map((row) => {
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
          <tbody>{rows}{rowsV2}</tbody>
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
