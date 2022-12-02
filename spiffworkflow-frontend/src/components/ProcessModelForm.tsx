import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
// @ts-ignore
import { Button, ButtonSet, Form, Stack, TextInput } from '@carbon/react';
// @ts-ignore
import { AddAlt } from '@carbon/icons-react';
import { modifyProcessIdentifierForPathParam, slugifyString } from '../helpers';
import HttpService from '../services/HttpService';
import { MetadataExtractionPaths, ProcessModel } from '../interfaces';

type OwnProps = {
  mode: string;
  processModel: ProcessModel;
  processGroupId?: string;
  setProcessModel: (..._args: any[]) => any;
};

export default function ProcessModelForm({
  mode,
  processModel,
  processGroupId,
  setProcessModel,
}: OwnProps) {
  const [identifierInvalid, setIdentifierInvalid] = useState<boolean>(false);
  const [idHasBeenUpdatedByUser, setIdHasBeenUpdatedByUser] =
    useState<boolean>(false);
  const [displayNameInvalid, setDisplayNameInvalid] = useState<boolean>(false);
  useState<boolean>(false);
  const navigate = useNavigate();

  const navigateToProcessModel = (result: ProcessModel) => {
    if ('id' in result) {
      const modifiedProcessModelPathFromResult =
        modifyProcessIdentifierForPathParam(result.id);
      navigate(`/admin/process-models/${modifiedProcessModelPathFromResult}`);
    }
  };

  const hasValidIdentifier = (identifierToCheck: string) => {
    return identifierToCheck.match(/^[a-z0-9][0-9a-z-]+[a-z0-9]$/);
  };

  const handleFormSubmission = (event: any) => {
    event.preventDefault();
    let hasErrors = false;
    if (mode === 'new' && !hasValidIdentifier(processModel.id)) {
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
    let path = `/process-models/${modifyProcessIdentifierForPathParam(
      processGroupId || ''
    )}`;
    let httpMethod = 'POST';
    if (mode === 'edit') {
      httpMethod = 'PUT';
      path = `/process-models/${modifyProcessIdentifierForPathParam(
        processModel.id
      )}`;
    }
    const postBody = {
      display_name: processModel.display_name,
      description: processModel.description,
      metadata_extraction_paths: processModel.metadata_extraction_paths,
    };
    if (mode === 'new') {
      Object.assign(postBody, {
        id: `${processGroupId}/${processModel.id}`,
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

  const metadataExtractionPathForm = (
    metadataKey: string,
    metadataPath: string
  ) => {
    return (
      <>
        <TextInput
          id="process-model-metadata-extraction-path-key"
          labelText="Extraction Key"
          value={metadataKey}
          onChange={(event: any) => {
            const cep: MetadataExtractionPaths =
              processModel.metadata_extraction_paths || {};
            delete cep[metadataKey];
            cep[event.target.value] = metadataPath;
            updateProcessModel({ metadata_extraction_paths: cep });
          }}
        />
        <TextInput
          id="process-model-metadata-extraction-path"
          labelText="Extraction Path"
          value={metadataPath}
          onChange={(event: any) => {
            const cep: MetadataExtractionPaths =
              processModel.metadata_extraction_paths || {};
            cep[metadataKey] = event.target.value;
            updateProcessModel({ metadata_extraction_paths: cep });
          }}
        />
      </>
    );
  };

  const metadataExtractionPathFormArea = () => {
    if (processModel.metadata_extraction_paths) {
      console.log(
        'processModel.metadata_extraction_paths',
        processModel.metadata_extraction_paths
      );
      return Object.keys(processModel.metadata_extraction_paths).map(
        (metadataKey: string) => {
          return metadataExtractionPathForm(
            metadataKey,
            processModel.metadata_extraction_paths
              ? processModel.metadata_extraction_paths[metadataKey]
              : ''
          );
        }
      );
    }
    return null;
  };

  const addBlankMetadataExtractionPath = () => {
    const cep: MetadataExtractionPaths =
      processModel.metadata_extraction_paths || {};
    Object.assign(cep, { '': '' });
    updateProcessModel({ metadata_extraction_paths: cep });
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

    textInputs.push(<>{metadataExtractionPathFormArea()}</>);
    textInputs.push(
      <Button
        data-qa="add-metadata-extraction-path-button"
        renderIcon={AddAlt}
        className="button-white-background"
        kind=""
        size="sm"
        onClick={() => {
          addBlankMetadataExtractionPath();
        }}
      >
        Add Metadata Extraction Path
      </Button>
    );

    return textInputs;
  };

  const formButtons = () => {
    const buttons = [
      <Button kind="secondary" type="submit">
        Submit
      </Button>,
    ];
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
