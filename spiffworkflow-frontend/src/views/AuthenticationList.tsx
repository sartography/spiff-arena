import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
} from '@mui/material';
import { AuthenticationItem } from '../interfaces';
import HttpService from '../services/HttpService';
import UserService from '../services/UserService';
import { BACKEND_BASE_URL } from '../config';
import AuthenticationConfiguration from '../components/AuthenticationConfiguration';

export default function AuthenticationList() {
  const [authenticationList, setAuthenticationList] = useState<
    AuthenticationItem[] | null
  >(null);
  const [authenticationV2List, setAuthenticationV2List] = useState<
    AuthenticationItem[] | null
  >(null);
  const [connectProxyBaseUrl, setConnectProxyBaseUrl] = useState<string | null>(
    null,
  );
  const [redirectUrl, setRedirectUrl] = useState<string | null>(null);
  const { t } = useTranslation();

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
          <TableRow key={row.id}>
            <TableCell>
              <a
                data-testid="authentication-create-link"
                href={`${connectProxyBaseUrl}/v1/auth/${
                  row.id
                }?redirect_url=${redirectUrl}/${
                  row.id
                }?token=${UserService.getAccessToken()}`}
              >
                {row.id}
              </a>
            </TableCell>
            <TableCell>Connector Proxy</TableCell>
          </TableRow>
        );
      });
      const rowsV2 = authenticationV2List.map((row) => {
        return (
          <TableRow key={row.id}>
            <TableCell>
              <a
                data-testid="authentication-create-link"
                href={`${BACKEND_BASE_URL}/authentication_begin/${
                  row.id
                }?token=${UserService.getAccessToken()}`}
              >
                {row.id}
              </a>
            </TableCell>
            <TableCell>{t('local_configuration')}</TableCell>
          </TableRow>
        );
      });
      return (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>{t('id')}</TableCell>
                <TableCell>{t('source')}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {rows}
              {rowsV2}
            </TableBody>
          </Table>
        </TableContainer>
      );
    }
    return null;
  };

  if (authenticationList) {
    return (
      <>
        <Typography variant="h1">{t('authentications')}</Typography>
        {buildTable()}
        <AuthenticationConfiguration />
      </>
    );
  }

  return null;
}
