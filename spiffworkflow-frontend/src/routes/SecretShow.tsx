import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
// @ts-ignore
import { Stack, Table, Button } from '@carbon/react';
import HttpService from '../services/HttpService';
import { Secret } from '../interfaces';
import ButtonWithConfirmation from '../components/ButtonWithConfirmation';

export default function SecretShow() {
  const navigate = useNavigate();
  const params = useParams();

  const [secret, setSecret] = useState<Secret | null>(null);
  const [secretValue, setSecretValue] = useState(secret?.value);

  useEffect(() => {
    HttpService.makeCallToBackend({
      path: `/secrets/${params.key}`,
      successCallback: setSecret,
    });
  }, [params]);

  const handleSecretValueChange = (event: any) => {
    if (secret) {
      setSecretValue(event.target.value);
    }
  };

  const updateSecretValue = () => {
    if (secret && secretValue) {
      secret.value = secretValue;
      HttpService.makeCallToBackend({
        path: `/secrets/${secret.key}`,
        successCallback: () => {
          setSecret(secret);
        },
        httpMethod: 'PUT',
        postBody: {
          value: secretValue,
          creator_user_id: secret.creator_user_id,
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

  if (secret) {
    return (
      <>
        <h1>Secret Key: {secret.key}</h1>
        <Stack orientation="horizontal" gap={3}>
          <ButtonWithConfirmation
            description="Delete Secret?"
            onConfirmation={deleteSecret}
            buttonLabel="Delete"
          />
          <Button variant="warning" onClick={updateSecretValue}>
            Update Value
          </Button>
        </Stack>
        <div>
          <Table striped bordered>
            <thead>
              <tr>
                <th>Key</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>{params.key}</td>
                <td>
                  <input
                    id="secret_value"
                    name="secret_value"
                    type="password"
                    value={secretValue || secret.value}
                    onChange={handleSecretValueChange}
                  />
                </td>
              </tr>
            </tbody>
          </Table>
        </div>
      </>
    );
  }
  return null;
}
