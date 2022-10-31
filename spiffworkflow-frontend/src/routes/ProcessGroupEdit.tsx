import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
// @ts-ignore
import { Button, Stack } from '@carbon/react';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import HttpService from '../services/HttpService';
import ButtonWithConfirmation from '../components/ButtonWithConfirmation';

export default function ProcessGroupEdit() {
  const [displayName, setDisplayName] = useState('');
  const params = useParams();
  const navigate = useNavigate();
  const [processGroup, setProcessGroup] = useState(null);

  useEffect(() => {
    const setProcessGroupsFromResult = (result: any) => {
      setProcessGroup(result);
      setDisplayName(result.display_name);
    };

    HttpService.makeCallToBackend({
      path: `/process-groups/${params.process_group_id}`,
      successCallback: setProcessGroupsFromResult,
    });
  }, [params]);

  const navigateToProcessGroup = (_result: any) => {
    navigate(`/admin/process-groups/${(processGroup as any).id}`);
  };

  const navigateToProcessGroups = (_result: any) => {
    navigate(`/admin/process-groups`);
  };

  const updateProcessGroup = (event: any) => {
    event.preventDefault();
    HttpService.makeCallToBackend({
      path: `/process-groups/${(processGroup as any).id}`,
      successCallback: navigateToProcessGroup,
      httpMethod: 'PUT',
      postBody: {
        display_name: displayName,
        id: (processGroup as any).id,
      },
    });
  };

  const deleteProcessGroup = () => {
    HttpService.makeCallToBackend({
      path: `/process-groups/${(processGroup as any).id}`,
      successCallback: navigateToProcessGroups,
      httpMethod: 'DELETE',
    });
  };

  const onDisplayNameChanged = (newDisplayName: any) => {
    setDisplayName(newDisplayName);
  };

  if (processGroup) {
    return (
      <>
        <ProcessBreadcrumb processGroupId={(processGroup as any).id} />
        <h2>Edit Process Group: {(processGroup as any).id}</h2>
        <form onSubmit={updateProcessGroup}>
          <label>Display Name:</label>
          <input
            name="display_name"
            type="text"
            value={displayName}
            onChange={(e) => onDisplayNameChanged(e.target.value)}
          />
          <br />
          <br />
          <Stack direction="horizontal" gap={3}>
            <Button type="submit">Submit</Button>
            <Button
              variant="secondary"
              href={`/admin/process-groups/${(processGroup as any).id}`}
            >
              Cancel
            </Button>
            <ButtonWithConfirmation
              description={`Delete Process Group ${(processGroup as any).id}?`}
              onConfirmation={deleteProcessGroup}
              buttonLabel="Delete"
            />
          </Stack>
        </form>
      </>
    );
  }
  return null;
}
