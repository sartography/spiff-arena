import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Form, Stack, TextInput, TextArea } from '@carbon/react';
import { modifyProcessIdentifierForPathParam, slugifyString } from '../helpers';
import HttpService from '../services/HttpService';
import { ProcessGroup } from '../interfaces';

import useProcessGroupFetcher from '../hooks/useProcessGroupFetcher';

type OwnProps = {
  mode: string;
  processGroup: ProcessGroup;
  setProcessGroup: (..._args: any[]) => any;
};

export default function ProcessGroupForm({
  mode,
  processGroup,
  setProcessGroup,
}: OwnProps) {
  const [identifierInvalid, setIdentifierInvalid] = useState<boolean>(false);
  const [idHasBeenUpdatedByUser, setIdHasBeenUpdatedByUser] =
    useState<boolean>(false);
  const [displayNameInvalid, setDisplayNameInvalid] = useState<boolean>(false);
  const navigate = useNavigate();
  let newProcessGroupId = processGroup.id;

  const { updateProcessGroupCache } = useProcessGroupFetcher(processGroup.id);

  const handleProcessGroupUpdateResponse = (_result: any) => {
    if (newProcessGroupId) {
      updateProcessGroupCache(processGroup);
      navigate(
        `/process-groups/${modifyProcessIdentifierForPathParam(
          newProcessGroupId,
        )}`,
      );
    }
  };

  const hasValidIdentifier = (identifierToCheck: string) => {
    return identifierToCheck.match(/^[a-z0-9][0-9a-z-]*[a-z0-9]$/);
  };

  const handleFormSubmission = (event: any) => {
    const searchParams = new URLSearchParams(document.location.search);
    const parentGroupId = searchParams.get('parentGroupId');

    event.preventDefault();
    let hasErrors = false;
    if (mode === 'new' && !hasValidIdentifier(processGroup.id)) {
      setIdentifierInvalid(true);
      hasErrors = true;
    }
    if (processGroup.display_name === '') {
      setDisplayNameInvalid(true);
      hasErrors = true;
    }
    if (hasErrors) {
      return;
    }
    let path = '/process-groups';
    if (mode === 'edit') {
      path = `/process-groups/${modifyProcessIdentifierForPathParam(
        processGroup.id,
      )}`;
    }
    let httpMethod = 'POST';
    if (mode === 'edit') {
      httpMethod = 'PUT';
    }
    const postBody = {
      display_name: processGroup.display_name,
      description: processGroup.description,
      messages: processGroup.messages,
    };
    if (mode === 'new') {
      if (parentGroupId) {
        newProcessGroupId = `${parentGroupId}/${processGroup.id}`;
      }
      Object.assign(postBody, {
        id: parentGroupId
          ? `${parentGroupId}/${processGroup.id}`
          : `${processGroup.id}`,
      });
    }

    HttpService.makeCallToBackend({
      path,
      successCallback: handleProcessGroupUpdateResponse,
      httpMethod,
      postBody,
    });
  };

  const updateProcessGroup = (newValues: any) => {
    const processGroupToCopy = {
      ...processGroup,
    };
    Object.assign(processGroupToCopy, newValues);
    setProcessGroup(processGroupToCopy);
  };

  const onDisplayNameChanged = (newDisplayName: any) => {
    setDisplayNameInvalid(false);
    const updateDict = { display_name: newDisplayName };
    if (!idHasBeenUpdatedByUser && mode === 'new') {
      Object.assign(updateDict, { id: slugifyString(newDisplayName) });
    }
    updateProcessGroup(updateDict);
  };

  const formElements = () => {
    const textInputs = [
      <TextInput
        id="process-group-display-name"
        data-qa="process-group-display-name-input"
        name="display_name"
        invalidText="Display Name is required."
        invalid={displayNameInvalid}
        labelText="Display Name*"
        value={processGroup.display_name}
        onChange={(event: any) => onDisplayNameChanged(event.target.value)}
      />,
    ];

    if (mode === 'new') {
      textInputs.push(
        <TextInput
          id="process-group-identifier"
          name="id"
          invalidText="Identifier is required and must be all lowercase characters and hyphens."
          invalid={identifierInvalid}
          labelText="Identifier*"
          value={processGroup.id}
          onChange={(event: any) => {
            updateProcessGroup({ id: event.target.value });
            // was invalid, and now valid
            if (identifierInvalid && hasValidIdentifier(event.target.value)) {
              setIdentifierInvalid(false);
            }
            setIdHasBeenUpdatedByUser(true);
          }}
        />,
      );
    }

    textInputs.push(
      <TextArea
        id="process-group-description"
        name="description"
        labelText="Description"
        value={processGroup.description}
        onChange={(event: any) =>
          updateProcessGroup({ description: event.target.value })
        }
      />,
    );
    return textInputs;
  };

  const formButtons = () => {
    return <Button type="submit">Submit</Button>;
  };

  return (
    <Form onSubmit={handleFormSubmission}>
      <Stack gap={5}>
        {formElements()}
        {formButtons()}
      </Stack>
    </Form>
  );
}
