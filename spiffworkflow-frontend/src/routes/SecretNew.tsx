import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Form, TextInput, Button, ButtonSet, Stack } from '@carbon/react';
import HttpService from '../services/HttpService';

export default function SecretNew() {
  const [value, setValue] = useState<string>('');
  const [key, setKey] = useState<string>('');
  const [keyIsInvalid, setKeyIsInvalid] = useState<boolean>(false);
  const [valueIsInvalid, setValueIsInvalid] = useState<boolean>(false);
  const navigate = useNavigate();

  const navigateToSecret = (_result: any) => {
    navigate(`/configuration/secrets/${key}`);
  };

  const navigateToSecrets = () => {
    navigate(`/configuration/secrets`);
  };

  const addSecret = (event: any) => {
    event.preventDefault();

    let hasErrors = false;
    setKeyIsInvalid(false);
    if (!key.match(/^[\w-]+$/)) {
      setKeyIsInvalid(true);
      hasErrors = true;
    }
    setValueIsInvalid(false);
    if (value.trim().length < 1) {
      setValueIsInvalid(true);
      hasErrors = true;
    }
    if (hasErrors) {
      return;
    }

    HttpService.makeCallToBackend({
      path: `/secrets`,
      successCallback: navigateToSecret,
      httpMethod: 'POST',
      postBody: {
        key,
        value,
      },
    });
  };

  return (
    <main style={{ padding: '1rem 0' }}>
      <h1>Add Secret</h1>
      <Form onSubmit={addSecret}>
        <Stack gap={5}>
          <TextInput
            id="secret-key"
            labelText="Key*"
            value={key}
            invalid={keyIsInvalid}
            invalidText="The key must be alphanumeric characters and underscores"
            onChange={(e: any) => setKey(e.target.value)}
          />
          <TextInput
            id="secret-value"
            labelText="Value*"
            value={value}
            invalid={valueIsInvalid}
            invalidText="The value must be set"
            onChange={(e: any) => {
              setValue(e.target.value);
            }}
          />
          <ButtonSet>
            <Button kind="tertiary" onClick={navigateToSecrets}>
              Cancel
            </Button>
            <Button kind="primary" type="submit">
              Submit
            </Button>
          </ButtonSet>
        </Stack>
      </Form>
    </main>
  );
}
