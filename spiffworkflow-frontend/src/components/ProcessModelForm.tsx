import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import {
  Button,
  TextField,
  Select,
  MenuItem,
  IconButton,
  Typography,
  FormControl,
  InputLabel,
} from '@mui/material';
import Grid from '@mui/material/Grid2';
import { Add as AddAlt, Delete as TrashCan } from '@mui/icons-material';
import { modifyProcessIdentifierForPathParam, slugifyString } from '../helpers';
import HttpService from '../services/HttpService';
import { MetadataExtractionPath, ProcessModel } from '../interfaces';
import SpiffTooltip from './SpiffTooltip';

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
  const { t } = useTranslation();
  const navigate = useNavigate();

  const navigateToProcessModel = (result: ProcessModel) => {
    if ('id' in result) {
      const modifiedProcessModelPathFromResult =
        modifyProcessIdentifierForPathParam(result.id);
      navigate(`/process-models/${modifiedProcessModelPathFromResult}`);
    }
  };

  const hasValidIdentifier = (identifierToCheck: string) => {
    return identifierToCheck.match(/^[a-z0-9][0-9a-z.-]+[a-z0-9]$/);
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
      <Grid container spacing={2} alignItems="center" sx={{ mb: 1 }}>
        <Grid size={{ xs: 3 }}>
          <TextField
            id={`process-model-metadata-extraction-path-key-${index}`}
            label={t('extraction_key')}
            value={metadataExtractionPath.key}
            onChange={(event: any) => {
              const cep: MetadataExtractionPath[] =
                processModel.metadata_extraction_paths || [];
              const newMeta = { ...metadataExtractionPath };
              newMeta.key = event.target.value;
              cep[index] = newMeta;
              updateProcessModel({ metadata_extraction_paths: cep });
            }}
            fullWidth
          />
        </Grid>
        <Grid size={{ xs: 6 }}>
          <TextField
            id={`process-model-metadata-extraction-path-${index}`}
            label={t('extraction_path')}
            value={metadataExtractionPath.path}
            onChange={(event: any) => {
              const cep: MetadataExtractionPath[] =
                processModel.metadata_extraction_paths || [];
              const newMeta = { ...metadataExtractionPath };
              newMeta.path = event.target.value;
              cep[index] = newMeta;
              updateProcessModel({ metadata_extraction_paths: cep });
            }}
            fullWidth
          />
        </Grid>
        <Grid size={{ xs: 1 }}>
          <SpiffTooltip title={t('remove_key')}>
            <IconButton
              aria-label={t('remove_key')}
              onClick={() => {
                const cep: MetadataExtractionPath[] =
                  processModel.metadata_extraction_paths || [];
                cep.splice(index, 1);
                updateProcessModel({ metadata_extraction_paths: cep });
              }}
            >
              <TrashCan />
            </IconButton>
          </SpiffTooltip>
        </Grid>
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
      <Grid container spacing={2} alignItems="center" sx={{ mb: 1 }}>
        <Grid size={{ xs: 10 }}>
          <TextField
            id={`process-model-notification-address-key-${index}`}
            label="Address"
            value={notificationAddress}
            onChange={(event: any) => {
              const notificationAddresses: string[] =
                processModel.exception_notification_addresses || [];
              notificationAddresses[index] = event.target.value;
              updateProcessModel({
                exception_notification_addresses: notificationAddresses,
              });
            }}
            fullWidth
          />
        </Grid>
        <Grid size={{ xs: 2 }}>
          <SpiffTooltip title={t('remove_address')}>
            <IconButton
              aria-label={t('remove_address')}
              onClick={() => {
                const notificationAddresses: string[] =
                  processModel.exception_notification_addresses || [];
                notificationAddresses.splice(index, 1);
                updateProcessModel({
                  exception_notification_addresses: notificationAddresses,
                });
              }}
            >
              <TrashCan />
            </IconButton>
          </SpiffTooltip>
        </Grid>
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
      <TextField
        id="process-model-display-name"
        key="process-model-display-name"
        name="display_name"
        error={displayNameInvalid}
        helperText={displayNameInvalid ? t('display_name_required') : ''}
        label={t('display_name')}
        value={processModel.display_name}
        onChange={(event: any) => {
          onDisplayNameChanged(event.target.value);
        }}
        fullWidth
        sx={{ mb: 2 }}
      />,
    ];

    if (mode === 'new') {
      textInputs.push(
        <TextField
          id="process-model-identifier"
          key="process-model-identifier"
          name="id"
          error={identifierInvalid}
          helperText={
            identifierInvalid ? t('identifier_validation_message') : ''
          }
          label={t('identifier')}
          value={processModel.id}
          onChange={(event: any) => {
            updateProcessModel({ id: event.target.value });
            // was invalid, and now valid
            if (identifierInvalid && hasValidIdentifier(event.target.value)) {
              setIdentifierInvalid(false);
            }
            setIdHasBeenUpdatedByUser(true);
          }}
          fullWidth
          sx={{ mb: 2 }}
        />,
      );
    }

    textInputs.push(
      <TextField
        id="process-model-description"
        key="process-model-description"
        name="description"
        label={t('description')}
        value={processModel.description}
        onChange={(event: any) =>
          updateProcessModel({ description: event.target.value })
        }
        multiline
        fullWidth
        sx={{ mb: 2 }}
      />,
    );

    textInputs.push(
      <FormControl fullWidth>
        {/* we need to set labels in both places apparently so it displays when no option is selected */}
        <InputLabel id="notification-type-select-label">
          {t('notification_type')}
        </InputLabel>
        <Select
          id="notification-type"
          key="notification-type"
          value={processModel.fault_or_suspend_on_exception}
          labelId="notification-type-select-label"
          label={t('notification_type')}
          onChange={(event: any) => {
            onNotificationTypeChanged(event.target.value);
          }}
          fullWidth
          sx={{ mb: 2 }}
        >
          <MenuItem value="fault">{t('fault')}</MenuItem>
          <MenuItem value="suspend">{t('suspend')}</MenuItem>
        </Select>
      </FormControl>,
    );
    textInputs.push(
      <Typography variant="h3" sx={{ mt: 2, mb: 1 }}>
        {t('notification_addresses')}
      </Typography>,
    );
    textInputs.push(
      <Typography variant="body2" sx={{ mb: 2 }}>
        {t('notification_addresses_help')}
      </Typography>,
    );
    textInputs.push(<>{notificationAddressFormArea()}</>);
    textInputs.push(
      <Button
        data-testid="add-notification-address-button"
        startIcon={<AddAlt />}
        variant="outlined"
        size="small"
        onClick={() => {
          addBlankNotificationAddress();
        }}
        sx={{ mt: 1, mb: 2 }}
      >
        {t('add_notification_address')}
      </Button>,
    );

    textInputs.push(
      <Typography variant="h3" sx={{ mt: 2, mb: 1 }}>
        {t('metadata_extractions')}
      </Typography>,
    );
    textInputs.push(
      <Typography variant="body2" sx={{ mb: 2 }}>
        {t('metadata_extractions_help')}
      </Typography>,
    );
    textInputs.push(<>{metadataExtractionPathFormArea()}</>);
    textInputs.push(
      <Button
        data-testid="add-metadata-extraction-path-button"
        startIcon={<AddAlt />}
        variant="outlined"
        size="small"
        onClick={() => {
          addBlankMetadataExtractionPath();
        }}
        sx={{ mt: 1, mb: 2 }}
      >
        {t('add_metadata_extraction_path')}
      </Button>,
    );

    return textInputs;
  };

  const formButtons = () => {
    return (
      <Grid container justifyContent="flex-start" sx={{ mt: 2 }}>
        <Grid>
          <Button variant="contained" type="submit">
            {t('submit')}
          </Button>
        </Grid>
      </Grid>
    );
  };

  return (
    <form onSubmit={handleFormSubmission}>
      {formElements()}
      {formButtons()}
    </form>
  );
}
