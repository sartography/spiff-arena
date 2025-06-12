import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  TextField,
  Paper,
} from '@mui/material';
import HttpService from '../services/HttpService';
import { PermissionsToCheck, Secret } from '../interfaces';
import { Notification } from '../components/Notification';
import ButtonWithConfirmation from '../components/ButtonWithConfirmation';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import { usePermissionFetcher } from '../hooks/PermissionService';
import { Can } from '../contexts/Can';

export default function SecretShow() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const params = useParams();

  const [secret, setSecret] = useState<Secret | null>(null);
  const [displaySecretValue, setDisplaySecretValue] = useState<boolean>(false);
  const [showSuccessNotification, setShowSuccessNotification] =
    useState<boolean>(false);

  const { targetUris } = useUriListForPermissions();
  const permissionRequestData: PermissionsToCheck = {
    [targetUris.secretShowPath]: ['PUT', 'DELETE', 'GET'],
    [targetUris.secretShowValuePath]: ['GET'],
  };
  const { ability, permissionsLoaded } = usePermissionFetcher(
    permissionRequestData,
  );

  useEffect(() => {
    HttpService.makeCallToBackend({
      path: `/secrets/${params.secret_identifier}`,
      successCallback: setSecret,
    });
  }, [params.secret_identifier]);

  const handleSecretValueChange = (event: any) => {
    if (secret) {
      const newSecret = { ...secret, value: event.target.value };
      setSecret(newSecret);
    }
  };

  const updateSecretValue = () => {
    if (secret) {
      HttpService.makeCallToBackend({
        path: `/secrets/${secret.key}`,
        successCallback: () => {
          setShowSuccessNotification(true);
        },
        httpMethod: 'PUT',
        postBody: {
          value: secret.value,
        },
      });
    }
  };

  const navigateToSecrets = (_result: any) => {
    navigate(`/configuration/secrets`);
  };

  const deleteSecret = () => {
    if (secret === null) {
      return;
    }
    HttpService.makeCallToBackend({
      path: `/secrets/${secret.key}`,
      successCallback: navigateToSecrets,
      httpMethod: 'DELETE',
    });
  };

  const successNotificationComponent = (
    <Notification
      title={t('secret_updated')}
      onClose={() => setShowSuccessNotification(false)}
    />
  );

  const handleShowSecretValue = () => {
    if (secret === null) {
      return;
    }
    HttpService.makeCallToBackend({
      path: `/secrets/show-value/${secret.key}`,
      successCallback: (result: Secret) => {
        setSecret(result);
        setDisplaySecretValue(true);
      },
    });
  };

  if (secret && permissionsLoaded) {
    return (
      <>
        {showSuccessNotification && successNotificationComponent}
        <h1>{t('secret_key')}: {secret.key}</h1>
        <Stack direction="row" spacing={3}>
          <Can I="DELETE" a={targetUris.secretShowPath} ability={ability}>
            <ButtonWithConfirmation
              description={t('delete_secret_confirmation')}
              onConfirmation={deleteSecret}
              buttonLabel={t('delete')}
            />
          </Can>
          <Can
            I="GET"
            a={targetUris.secretShowValuePath}
            ability={ability}
            passThrough
          >
            {(secretReadAllowed: boolean) => {
              if (secretReadAllowed) {
                return (
                  <Button
                    disabled={displaySecretValue}
                    variant="contained"
                    color="warning"
                    onClick={handleShowSecretValue}
                  >
                    {t('retrieve_secret_value')}
                  </Button>
                );
              }
              return (
                <Can I="PUT" a={targetUris.secretShowPath} ability={ability}>
                  <Button
                    disabled={displaySecretValue}
                    variant="contained"
                    color="warning"
                    onClick={() => setDisplaySecretValue(true)}
                  >
                    {t('edit_secret_value')}
                  </Button>
                </Can>
              );
            }}
          </Can>
        </Stack>
        <div>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>{t('key')}</TableCell>
                  {displaySecretValue && (
                    <>
                      <TableCell>{t('value')}</TableCell>
                      <TableCell>{t('actions')}</TableCell>
                    </>
                  )}
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>{params.secret_identifier}</TableCell>
                  {displaySecretValue && (
                    <>
                      <TableCell aria-label={t('secret_value')}>
                        <TextField
                          id="secret_value"
                          name="secret_value"
                          label={t('secret_value')}
                          value={secret.value}
                          onChange={handleSecretValueChange}
                          disabled={
                            !ability.can('PUT', targetUris.secretShowPath)
                          }
                        />
                      </TableCell>
                      <TableCell>
                        <Can
                          I="PUT"
                          a={targetUris.secretShowPath}
                          ability={ability}
                        >
                          {displaySecretValue && (
                            <Button
                              variant="contained"
                              color="warning"
                              onClick={updateSecretValue}
                            >
                              {t('update_value_button')}
                            </Button>
                          )}
                        </Can>
                      </TableCell>
                    </>
                  )}
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </div>
      </>
    );
  }
  return null;
}
