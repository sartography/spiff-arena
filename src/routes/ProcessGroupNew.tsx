import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import { slugifyString } from '../helpers';
import HttpService from '../services/HttpService';

export default function ProcessGroupNew() {
  const [identifier, setIdentifier] = useState('');
  const [idHasBeenUpdatedByUser, setIdHasBeenUpdatedByUser] = useState(false);
  const [displayName, setDisplayName] = useState('');
  const navigate = useNavigate();

  const navigateToProcessGroup = (_result: any) => {
    navigate(`/admin/process-groups/${identifier}`);
  };

  const addProcessGroup = (event: any) => {
    event.preventDefault();
    HttpService.makeCallToBackend({
      path: `/process-groups`,
      successCallback: navigateToProcessGroup,
      httpMethod: 'POST',
      postBody: {
        id: identifier,
        display_name: displayName,
      },
    });
  };

  const onDisplayNameChanged = (newDisplayName: any) => {
    setDisplayName(newDisplayName);
    if (!idHasBeenUpdatedByUser) {
      setIdentifier(slugifyString(newDisplayName));
    }
  };

  return (
    <>
      <ProcessBreadcrumb />
      <h2>Add Process Group</h2>
      <Form onSubmit={addProcessGroup}>
        <Form.Group className="mb-3" controlId="display_name">
          <Form.Label>Display Name:</Form.Label>
          <Form.Control
            type="text"
            name="display_name"
            value={displayName}
            onChange={(e) => onDisplayNameChanged(e.target.value)}
          />
        </Form.Group>
        <Form.Group className="mb-3" controlId="identifier">
          <Form.Label>ID:</Form.Label>
          <Form.Control
            type="text"
            name="id"
            value={identifier}
            onChange={(e) => {
              setIdentifier(e.target.value);
              setIdHasBeenUpdatedByUser(true);
            }}
          />
        </Form.Group>
        <Button variant="primary" type="submit">
          Submit
        </Button>
      </Form>
    </>
  );
}
