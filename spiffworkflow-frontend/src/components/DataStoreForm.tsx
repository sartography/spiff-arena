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
import { truncateString } from '../helpers';

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
  const [dataStoreTypes, setDataStoreTypes] = useState<[DataStoreType] | []>(
    []
  );
  const [selectedDataStoreType, setSelectedDataStoreType] =
    useState<DataStoreType | null>(null);
  const navigate = useNavigate();
  const newDataStoreId = dataStore.id;

  useEffect(() => {
    const handleSetDataStoreTypesCallback = (result: any) => {
      setDataStoreTypes(result);
    };

    HttpService.makeCallToBackend({
      path: '/data-stores/types',
      successCallback: handleSetDataStoreTypesCallback,
      httpMethod: 'GET',
    });
  }, [setDataStoreTypes]);

  const navigateToDataStores = (_result: any) => {
    if (newDataStoreId) {
      navigate(`/dataStores/${newDataStoreId}`);
    }
  };

  const hasValidIdentifier = (identifierToCheck: string) => {
    return identifierToCheck.match(/^[a-z0-9][0-9a-z-]*[a-z0-9]$/);
  };

  const handleFormSubmission = (event: any) => {
    // const searchParams = new URLSearchParams(document.location.search);
    // const parentGroupId = searchParams.get('parentGroupId');

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
      setTypeInvalid(true)
      hasErrors = true;
    }
    if (hasErrors) {
      return;
    }
    let path = '/data-stores';
    let httpMethod = 'POST';
    if (mode === 'edit') {
      path = `/data-stores/${dataStore.id}`;
      httpMethod = 'PUT';
    }
    const postBody = {
      id: dataStore.id,
      name: dataStore.name,
      description: dataStore.description,
      type: dataStore.type,
    };
    console.log(postBody);
    /*
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
    */

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

  const onNameChanged = (newName: any) => {
    setNameInvalid(false);
    const updateDict = { name: newName };
    if (!idHasBeenUpdatedByUser && mode === 'new') {
      Object.assign(updateDict, { id: newName });
    }
    updateDataStore(updateDict);
  };

  const onTypeChanged = (newType: any) => {
    setTypeInvalid(false);
    const newTypeSelection = newType.selectedItem;
    const updateDict = { type: newTypeSelection.name };
    updateDataStore(updateDict);
    setSelectedDataStoreType(newTypeSelection);
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

    if (mode === 'new') {
      textInputs.push(
        <TextInput
          id="data-store-identifier"
          name="id"
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
        />
      );
    }

    textInputs.push(
      <ComboBox
        onChange={onTypeChanged}
        id="data-store-type-select"
        data-qa="data-store-type-selection"
        items={dataStoreTypes}
        itemToString={(dataStoreType: DataStoreType) => {
          if (dataStoreType) {
            return `${dataStoreType.name} (${truncateString(dataStoreType.description, 75)})`;
          }
          return null;
        }}
        titleText="Type*"
        invalidText="Type is required."
	invalid={typeInvalid}
        placeholder="Choose the data store type"
        selectedItem={selectedDataStoreType}
      />
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
      />
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
