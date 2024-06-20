import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button,
  Form,
  Stack,
  TextInput,
  TextArea,
  Grid,
  Column,
  Select,
  SelectItem,
  // @ts-ignore
} from '@carbon/react';
// @ts-ignore
import { AddAlt, TrashCan } from '@carbon/icons-react';
import { modifyProcessIdentifierForPathParam, slugifyString } from '../helpers';
import HttpService from '../services/HttpService';
import { MetadataExtractionPath, ProcessModel } from '../interfaces';

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
      navigate(`/process-models/${modifiedProcessModelPathFromResult}`);
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
      processGroupId || '',
    )}`;
    let httpMethod = 'POST';
    if (mode === 'edit') {
      httpMethod = 'PUT';
      path = `/process-models/${modifyProcessIdentifierForPathParam(
        processModel.id,
      )}`;
    }
    const postBody = {
      display_name: processModel.display_name,
      description: processModel.description,
      metadata_extraction_paths: processModel.metadata_extraction_paths,
      fault_or_suspend_on_exception: processModel.fault_or_suspend_on_exception,
      exception_notification_addresses:
        processModel.exception_notification_addresses,
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
    index: number,
    metadataExtractionPath: MetadataExtractionPath,
  ) => {
    return (
      <Grid>
        <Column md={3} lg={7} sm={1}>
          <TextInput
            id={`process-model-metadata-extraction-path-key-${index}`}
            labelText="Extraction Key"
            value={metadataExtractionPath.key}
            onChange={(event: any) => {
              const cep: MetadataExtractionPath[] =
                processModel.metadata_extraction_paths || [];
              const newMeta = { ...metadataExtractionPath };
              newMeta.key = event.target.value;
              cep[index] = newMeta;
              updateProcessModel({ metadata_extraction_paths: cep });
            }}
          />
        </Column>
        <Column md={4} lg={8} sm={2}>
          <TextInput
            id={`process-model-metadata-extraction-path-${index}`}
            labelText="Extraction Path"
            value={metadataExtractionPath.path}
            onChange={(event: any) => {
              const cep: MetadataExtractionPath[] =
                processModel.metadata_extraction_paths || [];
              const newMeta = { ...metadataExtractionPath };
              newMeta.path = event.target.value;
              cep[index] = newMeta;
              updateProcessModel({ metadata_extraction_paths: cep });
            }}
          />
        </Column>
        <Column md={1} lg={1} sm={1}>
          <Button
            kind="ghost"
            renderIcon={TrashCan}
            iconDescription="Remove Key"
            hasIconOnly
            size="lg"
            className="with-extra-top-margin"
            onClick={() => {
              const cep: MetadataExtractionPath[] =
                processModel.metadata_extraction_paths || [];
              cep.splice(index, 1);
              updateProcessModel({ metadata_extraction_paths: cep });
            }}
          />
        </Column>
      </Grid>
    );
  };

  const metadataExtractionPathFormArea = () => {
    if (processModel.metadata_extraction_paths) {
      return processModel.metadata_extraction_paths.map(
        (metadataExtractionPath: MetadataExtractionPath, index: number) => {
          return metadataExtractionPathForm(index, metadataExtractionPath);
        },
      );
    }
    return null;
  };

  const addBlankMetadataExtractionPath = () => {
    const cep: MetadataExtractionPath[] =
      processModel.metadata_extraction_paths || [];
    cep.push({ key: '', path: '' });
    updateProcessModel({ metadata_extraction_paths: cep });
  };

  const notificationAddressForm = (
    index: number,
    notificationAddress: string,
  ) => {
    return (
      <Grid>
        <Column md={3} lg={7} sm={1}>
          <TextInput
            id={`process-model-notification-address-key-${index}`}
            labelText="Address"
            value={notificationAddress}
            onChange={(event: any) => {
              const notificationAddresses: string[] =
                processModel.exception_notification_addresses || [];
              notificationAddresses[index] = event.target.value;
              updateProcessModel({
                exception_notification_addresses: notificationAddresses,
              });
            }}
          />
        </Column>
        <Column md={1} lg={1} sm={1}>
          <Button
            kind="ghost"
            renderIcon={TrashCan}
            iconDescription="Remove Address"
            hasIconOnly
            size="lg"
            className="with-extra-top-margin"
            onClick={() => {
              const notificationAddresses: string[] =
                processModel.exception_notification_addresses || [];
              notificationAddresses.splice(index, 1);
              updateProcessModel({
                exception_notification_addresses: notificationAddresses,
              });
            }}
          />
        </Column>
      </Grid>
    );
  };

  const notificationAddressFormArea = () => {
    if (processModel.exception_notification_addresses) {
      return processModel.exception_notification_addresses.map(
        (notificationAddress: string, index: number) => {
          return notificationAddressForm(index, notificationAddress);
        },
      );
    }
    return null;
  };

  const addBlankNotificationAddress = () => {
    const notificationAddresses: string[] =
      processModel.exception_notification_addresses || [];
    notificationAddresses.push('');
    updateProcessModel({
      exception_notification_addresses: notificationAddresses,
    });
  };

  const onDisplayNameChanged = (newDisplayName: any) => {
    setDisplayNameInvalid(false);
    const updateDict = { display_name: newDisplayName };
    if (!idHasBeenUpdatedByUser && mode === 'new') {
      Object.assign(updateDict, { id: slugifyString(newDisplayName) });
    }
    updateProcessModel(updateDict);
  };

  const onNotificationTypeChanged = (newNotificationType: string) => {
    const updateDict = { fault_or_suspend_on_exception: newNotificationType };
    updateProcessModel(updateDict);
  };

  const formElements = () => {
    const textInputs = [
      <TextInput
        id="process-model-display-name"
        key="process-model-display-name"
        name="display_name"
        invalidText="Display Name is required."
        invalid={displayNameInvalid}
        labelText="Display Name*"
        value={processModel.display_name}
        onChange={(event: any) => {
          onDisplayNameChanged(event.target.value);
        }}
      />,
    ];

    if (mode === 'new') {
      textInputs.push(
        <TextInput
          id="process-model-identifier"
          key="process-model-identifier"
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
        />,
      );
    }

    textInputs.push(
      <TextArea
        id="process-model-description"
        key="process-model-description"
        name="description"
        labelText="Description"
        value={processModel.description}
        onChange={(event: any) =>
          updateProcessModel({ description: event.target.value })
        }
      />,
    );

    textInputs.push(
      <Select
        id="notification-type"
        key="notification-type"
        defaultValue={processModel.fault_or_suspend_on_exception}
        labelText="Notification Type"
        onChange={(event: any) => {
          onNotificationTypeChanged(event.target.value);
        }}
      >
        <SelectItem value="fault" text="Fault" />
        <SelectItem value="suspend" text="Suspend" />
      </Select>,
    );
    textInputs.push(<h2>Notification Addresses</h2>);
    textInputs.push(
      <Grid>
        <Column md={8} lg={16} sm={4}>
          <p className="data-table-description">
            You can provide one or more addresses to notify if this model fails.
          </p>
        </Column>
      </Grid>,
    );
    textInputs.push(<>{notificationAddressFormArea()}</>);
    textInputs.push(
      <Grid>
        <Column md={4} lg={8} sm={2}>
          <Button
            data-qa="add-notification-address-button"
            renderIcon={AddAlt}
            kind="tertiary"
            size="sm"
            onClick={() => {
              addBlankNotificationAddress();
            }}
          >
            Add Notification Address
          </Button>
        </Column>
      </Grid>,
    );

    textInputs.push(<h2>Metadata Extractions</h2>);
    textInputs.push(
      <Grid>
        <Column md={8} lg={16} sm={4}>
          <p className="data-table-description">
            You can provide one or more metadata extractions to pull data from
            your process instances to provide quick access in searches and
            perspectives.
          </p>
        </Column>
      </Grid>,
    );
    textInputs.push(<>{metadataExtractionPathFormArea()}</>);
    textInputs.push(
      <Grid>
        <Column md={4} lg={8} sm={2}>
          <Button
            data-qa="add-metadata-extraction-path-button"
            renderIcon={AddAlt}
            kind="tertiary"
            size="sm"
            onClick={() => {
              addBlankMetadataExtractionPath();
            }}
          >
            Add Metadata Extraction Path
          </Button>
        </Column>
      </Grid>,
    );

    return textInputs;
  };

  const formButtons = () => {
    return (
      <Button kind="primary" type="submit">
        Submit
      </Button>
    );
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
