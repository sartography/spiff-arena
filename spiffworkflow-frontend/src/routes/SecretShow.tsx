import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
// @ts-ignore
import { Stack, Table, Button, TextInput } from '@carbon/react';
import HttpService from '../services/HttpService';
import { Secret } from '../interfaces';
import { Notification } from '../components/Notification';
import ButtonWithConfirmation from '../components/ButtonWithConfirmation';

export default function SecretShow() {
  const navigate = useNavigate();
  const params = useParams();

  const [secret, setSecret] = useState<Secret | null>(null);
  const [displaySecretValue, setDisplaySecretValue] = useState<boolean>(false);
  const [showSuccessNotification, setShowSuccessNotification] =
    useState<boolean>(false);

  useEffect(() => {
    HttpService.makeCallToBackend({
      path: `/secrets/${params.key}`,
      successCallback: setSecret,
    });
  }, [params]);

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
    navigate(`/admin/configuration/secrets`);
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

  if (secret) {
    return (
      <>
        {showSuccessNotification && successNotificationComponent}
        <h1>Secret Key: {secret.key}</h1>
        <Stack orientation="horizontal" gap={3}>
          <ButtonWithConfirmation
            description="Delete Secret?"
            onConfirmation={deleteSecret}
            buttonLabel="Delete"
          />
          <Button
            disabled={displaySecretValue}
            variant="warning"
            onClick={() => {
              setDisplaySecretValue(true);
            }}
          >
            Retrieve secret value
          </Button>
        </Stack>
        <div>
          <Table striped bordered>
            <thead>
              <tr>
                <th>Key</th>
                {displaySecretValue && (
                  <>
                    <th>Value</th>
                    <th>Actions</th>
                  </>
                )}
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>{params.key}</td>
                {displaySecretValue && (
                  <>
                    <td>
                      <TextInput
                        id="secret_value"
                        name="secret_value"
                        value={secret.value}
                        onChange={handleSecretValueChange}
                      />
                    </td>
                    <td>
                      {displaySecretValue && (
                        <Button variant="warning" onClick={updateSecretValue}>
                          Update Value
                        </Button>
                      )}
                    </td>
                  </>
                )}
              </tr>
            </tbody>
          </Table>
        </div>
      </>
    );
  }
  return null;
}
