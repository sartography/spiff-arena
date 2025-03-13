import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  TextareaAutosize,
  Stack,
} from '@mui/material';
import HttpService from '../services/HttpService';
import { DataStore, DataStoreType } from '../interfaces';
import {
  modifyProcessIdentifierForPathParam,
  truncateString,
} from '../helpers';

type OwnProps = {
  mode: string;
  dataStore: DataStore;
  setDataStore: (..._args: any[]) => any;
};

export default function DataStoreForm({
  mode,
  dataStore,
  setDataStore,
}: OwnProps) {
  const [identifierInvalid, setIdentifierInvalid] = useState<boolean>(false);
  const [idHasBeenUpdatedByUser, setIdHasBeenUpdatedByUser] =
    useState<boolean>(false);
  const [nameInvalid, setNameInvalid] = useState<boolean>(false);
  const [typeInvalid, setTypeInvalid] = useState<boolean>(false);
  const [schemaInvalid, setSchemaInvalid] = useState<boolean>(false);
  const [dataStoreTypes, setDataStoreTypes] = useState<[DataStoreType] | []>(
    [],
  );
  const [selectedDataStoreType, setSelectedDataStoreType] =
    useState<DataStoreType | null>(null);
  const navigate = useNavigate();

  const dataStoreLocation = () => {
    const searchParams = new URLSearchParams(document.location.search);
    const parentGroupId = searchParams.get('parentGroupId');

    return parentGroupId ?? '/';
  };

  useEffect(() => {
    const handleSetDataStoreTypesCallback = (result: any) => {
      const dataStoreType = result.find((item: any) => {
        return item.type === dataStore.type;
      });
      setDataStoreTypes(result);
      setSelectedDataStoreType(dataStoreType ?? null);
    };

    HttpService.makeCallToBackend({
      path: '/data-stores/types',
      successCallback: handleSetDataStoreTypesCallback,
      httpMethod: 'GET',
    });
  }, [dataStore, setDataStoreTypes]);

  const navigateToDataStores = (_result: any) => {
    const location = dataStoreLocation();
    if (location !== '/') {
      navigate(
        `/process-groups/${modifyProcessIdentifierForPathParam(location)}`,
      );
    } else {
      navigate(`/process-groups`);
    }
  };

  const hasValidIdentifier = (identifierToCheck: string) => {
    return identifierToCheck.match(/^[a-z][0-9a-z_]*[a-z0-9]$/);
  };

  const handleFormSubmission = (event: any) => {
    const searchParams = new URLSearchParams(document.location.search);
    const parentGroupId = searchParams.get('parentGroupId');

    event.preventDefault();
    let hasErrors = false;
    if (mode === 'new' && !hasValidIdentifier(dataStore.id)) {
      setIdentifierInvalid(true);
      hasErrors = true;
    }
    if (dataStore.name === '') {
      setNameInvalid(true);
      hasErrors = true;
    }
    if (selectedDataStoreType === null) {
      setTypeInvalid(true);
      hasErrors = true;
    }
    if (dataStore.schema === '') {
      setSchemaInvalid(true);
      hasErrors = true;
    }
    if (hasErrors) {
      return;
    }
    const path = '/data-stores';
    let httpMethod = 'POST';
    if (mode === 'edit') {
      httpMethod = 'PUT';
    }
    const postBody = {
      id: dataStore.id,
      name: dataStore.name,
      description: dataStore.description,
      type: dataStore.type,
      schema: dataStore.schema,
      location: parentGroupId ?? '/',
    };

    HttpService.makeCallToBackend({
      path,
      successCallback: navigateToDataStores,
      httpMethod,
      postBody,
    });
  };

  const updateDataStore = (newValues: any) => {
    const dataStoreToCopy = {
      ...dataStore,
    };
    Object.assign(dataStoreToCopy, newValues);
    setDataStore(dataStoreToCopy);
  };

  const makeIdentifier = (str: any) => {
    return str
      .toLowerCase()
      .trim()
      .replace(/[^\w\s-]/g, '')
      .replace(/[\s-]+/g, '_')
      .replace(/^[-\d]+/g, '')
      .replace(/-+$/g, '');
  };

  const onNameChanged = (newName: any) => {
    setNameInvalid(false);
    const updateDict = { name: newName };
    if (!idHasBeenUpdatedByUser && mode === 'new') {
      Object.assign(updateDict, { id: makeIdentifier(newName) });
    }
    updateDataStore(updateDict);
  };

  const onTypeChanged = (event: any) => {
    setTypeInvalid(false);
    const newTypeSelection = event.target.value;
    if (newTypeSelection) {
      const updateDict = { type: newTypeSelection };
      updateDataStore(updateDict);
    }
    setSelectedDataStoreType(newTypeSelection);
  };

  const onSchemaChanged = (newSchema: any) => {
    setSchemaInvalid(false);
    const updateDict = { schema: newSchema };
    updateDataStore(updateDict);
  };

  const dataStoreTypeDisplayString = (
    dataStoreType: DataStoreType | null,
  ): string => {
    if (dataStoreType) {
      return `${dataStoreType.name} (${truncateString(
        dataStoreType.description,
        75,
      )})`;
    }
    return '';
  };

  const formElements = () => {
    const textInputs = [
      <TextField
        id="data-store-name"
        data-qa="data-store-name-input"
        name="name"
        error={nameInvalid}
        helperText={nameInvalid ? 'Name is required.' : ''}
        label="Name*"
        value={dataStore.name}
        onChange={(event: any) => onNameChanged(event.target.value)}
      />,
    ];

    textInputs.push(
      <TextField
        id="data-store-identifier"
        name="id"
        InputProps={{
          readOnly: mode === 'edit',
        }}
        error={identifierInvalid}
        helperText={
          identifierInvalid
            ? 'Identifier is required and must be all lowercase characters and hyphens.'
            : ''
        }
        label="Identifier*"
        value={dataStore.id}
        onChange={(event: any) => {
          updateDataStore({ id: event.target.value });
          if (identifierInvalid && hasValidIdentifier(event.target.value)) {
            setIdentifierInvalid(false);
          }
          setIdHasBeenUpdatedByUser(true);
        }}
      />,
    );

    if (mode === 'edit') {
      textInputs.push(
        <TextField
          id="data-store-type"
          name="data-store-type"
          InputProps={{
            readOnly: true,
          }}
          label="Type*"
          value={dataStoreTypeDisplayString(selectedDataStoreType)}
        />,
      );
    } else {
      textInputs.push(
        <FormControl fullWidth error={typeInvalid}>
          <InputLabel id="data-store-type-select-label">Type*</InputLabel>
          <Select
            labelId="data-store-type-select-label"
            id="data-store-type-select"
            value={selectedDataStoreType ? selectedDataStoreType.type : ''}
            onChange={onTypeChanged}
            label="Type*"
          >
            {dataStoreTypes.map((type) => (
              <MenuItem key={type.type} value={type.type}>
                {dataStoreTypeDisplayString(type)}
              </MenuItem>
            ))}
          </Select>
        </FormControl>,
      );
    }

    textInputs.push(
      <TextField
        id="data-store-schema"
        name="schema"
        error={schemaInvalid}
        helperText={
          schemaInvalid ? 'Schema is required and must be valid JSON.' : ''
        }
        label="Schema*"
        multiline
        minRows={3}
        value={dataStore.schema}
        onChange={(event: any) => onSchemaChanged(event.target.value)}
      />,
    );

    textInputs.push(
      <InputLabel id="data-store-description-label">Description:</InputLabel>,
    );
    textInputs.push(
      <TextareaAutosize
        id="data-store-description"
        name="description"
        minRows={5}
        aria-label="Description"
        placeholder="Description"
        value={dataStore.description || ''}
        onChange={(event: any) =>
          updateDataStore({ description: event.target.value })
        }
      />,
    );

    return textInputs;
  };

  const formButtons = () => {
    return (
      <Button type="submit" variant="contained">
        Submit
      </Button>
    );
  };

  return (
    <form onSubmit={handleFormSubmission}>
      <Stack spacing={2}>
        {formElements()}
        {formButtons()}
      </Stack>
    </form>
  );
}
