import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import { slugifyString } from '../helpers';
import HttpService from '../services/HttpService';

export default function ProcessModelNew() {
  const params = useParams();

  const [identifier, setIdentifier] = useState('');
  const [idHasBeenUpdatedByUser, setIdHasBeenUpdatedByUser] = useState(false);
  const [displayName, setDisplayName] = useState('');
  const navigate = useNavigate();

  const navigateToNewProcessModel = (_result: any) => {
    navigate(`/admin/process-models/${params.process_group_id}/${identifier}`);
  };

  const addProcessModel = (event: any) => {
    event.preventDefault();
    HttpService.makeCallToBackend({
      path: `/process-models`,
      successCallback: navigateToNewProcessModel,
      httpMethod: 'POST',
      postBody: {
        id: `${params.process_group_id}/${identifier}`,
        display_name: displayName,
        description: displayName,
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
      <h2>Add Process Model</h2>
      <Form onSubmit={addProcessModel}>
        <Form.Group className="mb-3" controlId="display_name">
          <Form.Label>Display Name:</Form.Label>
          <Form.Control
            name="display_name"
            type="text"
            value={displayName}
            onChange={(e) => onDisplayNameChanged(e.target.value)}
          />
        </Form.Group>
        <Form.Group className="mb-3" controlId="identifier">
          <Form.Label>ID:</Form.Label>
          <Form.Control
            name="id"
            type="text"
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
