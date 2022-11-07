import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
// @ts-ignore
import { Stack } from '@carbon/react';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import HttpService from '../services/HttpService';

export default function SecretNew() {
  const [value, setValue] = useState('');
  const [key, setKey] = useState('');
  const navigate = useNavigate();

  const navigateToSecret = (_result: any) => {
    navigate(`/admin/secrets/${key}`);
  };

  const navigateToSecrets = () => {
    navigate(`/admin/secrets`);
  };

  const changeSpacesToDash = (someString: string) => {
    // change spaces to `-`
    let s1 = someString.replace(' ', '-');
    // remove any trailing `-`
    s1 = s1.replace(/-$/, '');
    return s1;
  };

  const addSecret = (event: any) => {
    event.preventDefault();
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

  const warningStyle = {
    color: 'red',
  };

  return (
    <main style={{ padding: '1rem 0' }}>
      <h2>Add Secret</h2>
      <Form onSubmit={addSecret}>
        <Form.Group className="mb-3" controlId="formDisplayName">
          <Form.Label>
            Key: <span style={warningStyle}>No Spaces</span>
          </Form.Label>
          <Form.Control
            type="text"
            value={key}
            onChange={(e) => setKey(changeSpacesToDash(e.target.value))}
          />
        </Form.Group>
        <Form.Group className="mb-3" controlId="formIdentifier">
          <Form.Label>Value:</Form.Label>
          <Form.Control
            type="text"
            value={value}
            onChange={(e) => {
              setValue(e.target.value);
            }}
          />
        </Form.Group>
        <Stack orientation="horizontal" gap={3}>
          <Button variant="primary" type="submit">
            Submit
          </Button>
          <Button variant="danger" type="button" onClick={navigateToSecrets}>
            Cancel
          </Button>
        </Stack>
      </Form>
    </main>
  );
}
