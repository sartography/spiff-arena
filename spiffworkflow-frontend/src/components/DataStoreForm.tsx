import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
// @ts-ignore
import {
  Button,
  ComboBox,
  Form,
  Stack,
  TextInput,
  TextArea,
} from '@carbon/react';
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

  const onTypeChanged = (newType: any) => {
    setTypeInvalid(false);
    const newTypeSelection = newType.selectedItem;
    if (
      newTypeSelection &&
      typeof newTypeSelection === 'object' &&
      'type' in newTypeSelection
    ) {
      const updateDict = { type: newTypeSelection.type };
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
      <TextInput
        id="data-store-name"
        data-qa="data-store-name-input"
        name="name"
        invalidText="Name is required."
        invalid={nameInvalid}
        labelText="Name*"
        value={dataStore.name}
        onChange={(event: any) => onNameChanged(event.target.value)}
      />,
    ];

    textInputs.push(
      <TextInput
        id="data-store-identifier"
        name="id"
        readonly={mode === 'edit'}
        invalidText="Identifier is required and must be all lowercase characters and hyphens."
        invalid={identifierInvalid}
        labelText="Identifier*"
        value={dataStore.id}
        onChange={(event: any) => {
          updateDataStore({ id: event.target.value });
          // was invalid, and now valid
          if (identifierInvalid && hasValidIdentifier(event.target.value)) {
            setIdentifierInvalid(false);
          }
          setIdHasBeenUpdatedByUser(true);
        }}
      />,
    );

    if (mode === 'edit') {
      textInputs.push(
        <TextInput
          id="data-store-type"
          name="data-store-type"
          readonly
          labelText="Type*"
          value={dataStoreTypeDisplayString(selectedDataStoreType)}
        />,
      );
    } else {
      textInputs.push(
        <ComboBox
          onChange={onTypeChanged}
          id="data-store-type-select"
          data-qa="data-store-type-selection"
          items={dataStoreTypes}
          itemToString={dataStoreTypeDisplayString}
          titleText="Type*"
          invalidText="Type is required."
          invalid={typeInvalid}
          placeholder="Choose the data store type"
          selectedItem={selectedDataStoreType}
        />,
      );
    }

    textInputs.push(
      <TextArea
        id="data-store-schema"
        name="schema"
        invalidText="Schema is required and must be valid JSON."
        invalid={schemaInvalid}
        labelText="Schema*"
        value={dataStore.schema}
        onChange={(event: any) => onSchemaChanged(event.target.value)}
      />,
    );

    textInputs.push(
      <TextArea
        id="data-store-description"
        name="description"
        labelText="Description"
        value={dataStore.description}
        onChange={(event: any) =>
          updateDataStore({ description: event.target.value })
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
