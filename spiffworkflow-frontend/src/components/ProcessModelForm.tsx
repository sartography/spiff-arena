import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
// @ts-ignore
import { Button, ButtonSet, Form, Stack, TextInput } from '@carbon/react';
import {
  getGroupFromModifiedModelId,
  modifyProcessModelPath,
  slugifyString,
} from '../helpers';
import HttpService from '../services/HttpService';
import { ProcessModel } from '../interfaces';
import ButtonWithConfirmation from './ButtonWithConfirmation';

type OwnProps = {
  mode: string;
  processModel: ProcessModel;
  setProcessModel: (..._args: any[]) => any;
};

export default function ProcessModelForm({
  mode,
  processModel,
  setProcessModel,
}: OwnProps) {
  const [identifierInvalid, setIdentifierInvalid] = useState<boolean>(false);
  const [idHasBeenUpdatedByUser, setIdHasBeenUpdatedByUser] =
    useState<boolean>(false);
  const [displayNameInvalid, setDisplayNameInvalid] = useState<boolean>(false);
  const navigate = useNavigate();
  const modifiedProcessModelPath = modifyProcessModelPath(processModel.id);

  const navigateToProcessModel = (_result: any) => {
    if (processModel) {
      navigate(`/admin/process-models/${modifiedProcessModelPath}`);
    }
  };

  const navigateToProcessModels = (_result: any) => {
    navigate(
      `/admin/process-groups/${getGroupFromModifiedModelId(
        modifiedProcessModelPath
      )}`
    );
  };

  const hasValidIdentifier = (identifierToCheck: string) => {
    return identifierToCheck.match(/^[a-z0-9][0-9a-z-]+[a-z0-9]$/);
  };

  const deleteProcessModel = () => {
    HttpService.makeCallToBackend({
      path: `/process-models/${modifiedProcessModelPath}`,
      successCallback: navigateToProcessModels,
      httpMethod: 'DELETE',
    });
  };

  const handleFormSubmission = (event: any) => {
    event.preventDefault();
    let hasErrors = false;
    if (!hasValidIdentifier(processModel.id)) {
      setIdentifierInvalid(true);
      hasErrors = true;
    }
    if (processModel.display_name === '') {
      setDisplayNameInvalid(true);
      hasErrors = true;
    }
    if (hasErrors) {
      return;
    }
    let path = `/process-models`;
    if (mode === 'edit') {
      path = `/process-models/${modifiedProcessModelPath}`;
    }
    let httpMethod = 'POST';
    if (mode === 'edit') {
      httpMethod = 'PUT';
    }
    const postBody = {
      display_name: processModel.display_name,
      description: processModel.description,
    };
    if (mode === 'new') {
      Object.assign(postBody, {
        id: processModel.id,
      });
    }

    HttpService.makeCallToBackend({
      path,
      successCallback: navigateToProcessModel,
      httpMethod,
      postBody,
    });
  };

  const updateProcessModel = (newValues: any) => {
    const processModelToCopy = {
      ...processModel,
    };
    Object.assign(processModelToCopy, newValues);
    setProcessModel(processModelToCopy);
  };

  const onDisplayNameChanged = (newDisplayName: any) => {
    setDisplayNameInvalid(false);
    const updateDict = { display_name: newDisplayName };
    if (!idHasBeenUpdatedByUser && mode === 'new') {
      Object.assign(updateDict, { id: slugifyString(newDisplayName) });
    }
    updateProcessModel(updateDict);
  };

  const formElements = () => {
    const textInputs = [
      <TextInput
        id="process-model-display-name"
        name="display_name"
        invalidText="Display Name is required."
        invalid={displayNameInvalid}
        labelText="Display Name*"
        value={processModel.display_name}
        onChange={(event: any) => {
          onDisplayNameChanged(event.target.value);
        }}
        onBlur={(event: any) => console.log('event', event)}
      />,
    ];

    if (mode === 'new') {
      textInputs.push(
        <TextInput
          id="process-model-identifier"
          name="id"
          invalidText="Identifier is required and must be all lowercase characters and hyphens."
          invalid={identifierInvalid}
          labelText="Identifier*"
          value={processModel.id}
          onChange={(event: any) => {
            updateProcessModel({ id: event.target.value });
            // was invalid, and now valid
            if (identifierInvalid && hasValidIdentifier(event.target.value)) {
              setIdentifierInvalid(false);
            }
            setIdHasBeenUpdatedByUser(true);
          }}
        />
      );
    }

    textInputs.push(
      <TextInput
        id="process-model-description"
        name="description"
        labelText="Description"
        value={processModel.description}
        onChange={(event: any) =>
          updateProcessModel({ description: event.target.value })
        }
      />
    );

    return textInputs;
  };

  const formButtons = () => {
    const buttons = [
      <Button kind="secondary" type="submit">
        Submit
      </Button>,
    ];
    if (mode === 'edit') {
      buttons.push(
        <ButtonWithConfirmation
          description={`Delete Process Model ${processModel.id}?`}
          onConfirmation={deleteProcessModel}
          buttonLabel="Delete"
          confirmButtonLabel="Delete"
        />
      );
    }
    return <ButtonSet>{buttons}</ButtonSet>;
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
