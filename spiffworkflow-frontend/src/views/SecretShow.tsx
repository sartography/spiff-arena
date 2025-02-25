import { useEffect, useState } from 'react';
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
      title="Secret updated"
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
        <h1>Secret Key: {secret.key}</h1>
        <Stack direction="row" spacing={3}>
          <Can I="DELETE" a={targetUris.secretShowPath} ability={ability}>
            <ButtonWithConfirmation
              description="Delete Secret?"
              onConfirmation={deleteSecret}
              buttonLabel="Delete"
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
                    Retrieve secret value
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
                    Edit secret value
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
                  <TableCell>Key</TableCell>
                  {displaySecretValue && (
                    <>
                      <TableCell>Value</TableCell>
                      <TableCell>Actions</TableCell>
                    </>
                  )}
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>{params.secret_identifier}</TableCell>
                  {displaySecretValue && (
                    <>
                      <TableCell aria-label="Secret value">
                        <TextField
                          id="secret_value"
                          name="secret_value"
                          label="Secret value"
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
                              Update Value
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
