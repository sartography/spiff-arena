import { useEffect, useState } from 'react';
// @ts-ignore
import { Button, ButtonSet, Form, Stack, TextInput } from '@carbon/react';
import { useParams } from 'react-router-dom';
import { FormField } from '../interfaces';
import { modifyProcessModelPath, slugifyString } from '../helpers';
import HttpService from '../services/HttpService';

export default function JsonSchemaFormBuilder() {
  const params = useParams();
  const [formTitle, setFormTitle] = useState<string>('');
  const [formDescription, setFormDescription] = useState<string>('');
  const [formId, setFormId] = useState<string>('');
  const [formFields, setFormFields] = useState<FormField[]>([]);
  const [showNewFormField, setShowNewFormField] = useState<boolean>(false);
  const [formIdHasBeenUpdatedByUser, setFormIdHasBeenUpdatedByUser] =
    useState<boolean>(false);
  const [formFieldIdHasBeenUpdatedByUser, setFormFieldIdHasBeenUpdatedByUser] =
    useState<boolean>(false);

  const [formFieldId, setFormFieldId] = useState<string>('');
  const [formFieldTitle, setFormFieldTitle] = useState<string>('');

  const modifiedProcessModelId = modifyProcessModelPath(
    `${params.process_model_id}`
  );

  useEffect(() => {}, []);

  const renderFormJson = () => {
    const formJson = {
      title: formTitle,
      description: formDescription,
      properties: {},
      required: [],
    };
    formFields.forEach((formField: FormField) => {
      (formJson.properties as any)[formField.id] = {
        type: 'string',
        title: formField.title,
      };
    });

    return JSON.stringify(formJson, null, 2);
  };

  const renderFormUiJson = () => {
    const uiOrder = formFields.map((formField: FormField) => {
      return formField.id;
    });
    return JSON.stringify({ 'ui:order': uiOrder }, null, 2);
  };

  const onFormFieldTitleChange = (newFormFieldTitle: string) => {
    console.log('newFormFieldTitle', newFormFieldTitle);
    console.log(
      'setFormFieldIdHasBeenUpdatedByUser',
      formFieldIdHasBeenUpdatedByUser
    );
    if (!formFieldIdHasBeenUpdatedByUser) {
      setFormFieldId(slugifyString(newFormFieldTitle));
    }
    setFormFieldTitle(newFormFieldTitle);
  };

  const onFormTitleChange = (newFormTitle: string) => {
    if (!formIdHasBeenUpdatedByUser) {
      setFormId(slugifyString(newFormTitle));
    }
    setFormTitle(newFormTitle);
  };

  const createNewFormField = () => {
    const newFormField: FormField = {
      id: formFieldId,
      title: formFieldTitle,
      required: false,
    };

    setFormFieldIdHasBeenUpdatedByUser(false);
    setShowNewFormField(false);
    setFormFields([...formFields, newFormField]);
  };

  const newFormFieldComponent = () => {
    if (showNewFormField) {
      return (
        <>
          <TextInput
            id="form-field-title"
            name="title"
            labelText="Title"
            value={formFieldTitle}
            onChange={(event: any) => {
              onFormFieldTitleChange(event.srcElement.value);
            }}
          />
          <TextInput
            id="json-form-field-id"
            name="id"
            labelText="ID"
            value={formFieldId}
            onChange={(event: any) => {
              setFormFieldIdHasBeenUpdatedByUser(true);
              setFormFieldId(event.srcElement.value);
            }}
          />
          <Button onClick={createNewFormField}>Add Field</Button>
        </>
      );
    }
    return null;
  };

  const formFieldArea = () => {
    if (formFields.length > 0) {
      return formFields.map((formField: FormField) => {
        return <p>Form Field: {formField.id}</p>;
      });
    }
    return null;
  };

  const handleSaveCallback = (result: any) => {
    console.log('result', result);
  };

  const uploadFile = (file: File) => {
    const url = `/process-models/${modifiedProcessModelId}/files`;
    const httpMethod = 'POST';
    const formData = new FormData();
    formData.append('file', file);
    formData.append('fileName', file.name);

    HttpService.makeCallToBackend({
      path: url,
      successCallback: handleSaveCallback,
      httpMethod,
      postBody: formData,
    });
  };

  const saveFile = () => {
    const formJsonFileName = `${formId}-schema.json`;
    const formUiJsonFileName = `${formId}-uischema.json`;

    uploadFile(new File([renderFormJson()], formJsonFileName));
    uploadFile(new File([renderFormUiJson()], formUiJsonFileName));
  };

  const jsonFormArea = () => {
    return (
      <>
        <Button onClick={saveFile}>Save</Button>
        <TextInput
          id="json-form-title"
          name="title"
          labelText="Title"
          value={formTitle}
          onChange={(event: any) => {
            onFormTitleChange(event.srcElement.value);
          }}
        />
        <TextInput
          id="json-form-id"
          name="id"
          labelText="ID"
          value={formId}
          onChange={(event: any) => {
            setFormIdHasBeenUpdatedByUser(true);
            setFormId(event.srcElement.value);
          }}
        />
        <TextInput
          id="form-description"
          name="description"
          labelText="Description"
          value={formDescription}
          onChange={(event: any) => {
            setFormDescription(event.srcElement.value);
          }}
        />
        <Button
          onClick={() => {
            setFormFieldId('');
            setFormFieldTitle('');
            setShowNewFormField(true);
          }}
        >
          New Field
        </Button>
        {formFieldArea()}
        {newFormFieldComponent()}
      </>
    );
  };

  return <>{jsonFormArea()}</>;
}
