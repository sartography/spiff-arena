import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
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

  return (
    <main style={{ padding: '1rem 0' }}>
      <h2>Add Secret</h2>
      <Form onSubmit={addSecret}>
        <Form.Group className="mb-3" controlId="formDisplayName">
          <Form.Label>Key:</Form.Label>
          <Form.Control
            type="text"
            value={key}
            onChange={(e) => setKey(e.target.value)}
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
        <Button variant="primary" type="submit">
          Submit
        </Button>
      </Form>
    </main>
  );
}
