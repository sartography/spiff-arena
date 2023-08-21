import { useEffect, useState } from 'react';
// @ts-ignore
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import {
  Button,
  Select,
  SelectItem,
  TextInput,
  TextArea,
  Grid,
  Column,
  // @ts-ignore
} from '@carbon/react';
import validator from '@rjsf/validator-ajv8';
import { FormField, JsonSchemaForm } from '../interfaces';
import { Form } from '../rjsf/carbon_theme';
import {
  modifyProcessIdentifierForPathParam,
  slugifyString,
  underscorizeString,
} from '../helpers';
import HttpService from '../services/HttpService';
import { Notification } from '../components/Notification';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import ButtonWithConfirmation from '../components/ButtonWithConfirmation';

export default function JsonSchemaFormBuilder() {
  const params = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const formFieldTypes = ['textbox', 'checkbox', 'select'];

  const [formTitle, setFormTitle] = useState<string>('');
  const [formDescription, setFormDescription] = useState<string>('');
  const [formId, setFormId] = useState<string>('');
  const [formFields, setFormFields] = useState<FormField[]>([]);
  const [showNewFormField, setShowNewFormField] = useState<boolean>(false);
  const [formFieldSelectOptions, setFormFieldSelectOptions] =
    useState<string>('');
  const [formIdHasBeenUpdatedByUser, setFormIdHasBeenUpdatedByUser] =
    useState<boolean>(false);
  const [formFieldIdHasBeenUpdatedByUser, setFormFieldIdHasBeenUpdatedByUser] =
    useState<boolean>(false);
  const [showFormFieldSelectTextField, setShowFormFieldSelectTextField] =
    useState<boolean>(false);

  const [formFieldId, setFormFieldId] = useState<string>('');
  const [formFieldTitle, setFormFieldTitle] = useState<string>('');
  const [formFieldType, setFormFieldType] = useState<string>('');
  const [requiredFields, setRequiredFields] = useState<string[]>([]);
  const [savedJsonSchema, setSavedJsonSchema] = useState<boolean>(false);

  const modifiedProcessModelId = modifyProcessIdentifierForPathParam(
    `${params.process_model_id}`
  );

  useEffect(() => {
    const processResult = (result: JsonSchemaForm) => {
      const jsonForm = JSON.parse(result.file_contents);
      setFormTitle(jsonForm.title);
      setFormDescription(jsonForm.description);
      setRequiredFields(jsonForm.required);
      const newFormId = (searchParams.get('file_name') || '').replace(
        '-schema.json',
        ''
      );
      setFormId(newFormId);
      const newFormFields: FormField[] = [];
      Object.keys(jsonForm.properties).forEach((propertyId: string) => {
        const propertyDetails = jsonForm.properties[propertyId];
        newFormFields.push({
          id: propertyId,
          title: propertyDetails.title,
          required: propertyDetails.required,
          type: propertyDetails.type,
          enum: propertyDetails.enum,
          default: propertyDetails.default,
          pattern: propertyDetails.pattern,
        });
      });
      setFormFields(newFormFields);
    };
    if (searchParams.get('file_name')) {
      HttpService.makeCallToBackend({
        path: `/process-models/${modifiedProcessModelId}/files/${searchParams.get(
          'file_name'
        )}`,
        successCallback: processResult,
      });
    }
  }, [modifiedProcessModelId, searchParams]);

  const formSubmitResultElement = () => {
    if (savedJsonSchema) {
      return (
        <Notification
          title="Form Saved"
          onClose={() => setSavedJsonSchema(false)}
        >
          It saved
        </Notification>
      );
    }
    return null;
  };

  const renderFormJson = () => {
    const formJson = {
      title: formTitle,
      description: formDescription,
      properties: {},
      required: requiredFields,
    };

    formFields.forEach((formField: FormField) => {
      let jsonSchemaFieldType = formField.type;
      if (['checkbox'].includes(formField.type)) {
        jsonSchemaFieldType = 'boolean';
      }
      const formJsonObject: any = {
        type: jsonSchemaFieldType || 'string',
        title: formField.title,
      };

      if (formField.enum) {
        formJsonObject.enum = formField.enum;
      }
      if (formField.default !== undefined) {
        formJsonObject.default = formField.default;
      }
      if (formField.pattern) {
        formJsonObject.pattern = formField.pattern;
      }
      (formJson.properties as any)[formField.id] = formJsonObject;
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
    if (!formFieldIdHasBeenUpdatedByUser) {
      setFormFieldId(underscorizeString(newFormFieldTitle));
    }
    setFormFieldTitle(newFormFieldTitle);
  };

  const onFormTitleChange = (newFormTitle: string) => {
    if (!formIdHasBeenUpdatedByUser) {
      setFormId(slugifyString(newFormTitle));
    }
    setFormTitle(newFormTitle);
  };

  const getFormFieldType = (indicatedType: string) => {
    if (indicatedType === 'checkbox') {
      return 'boolean';
    }
    // undefined or 'select' or 'textbox'
    return 'string';
  };

  const addFormField = () => {
    const newFormField: FormField = {
      id: formFieldId,
      title: formFieldTitle,
      required: false,
      type: getFormFieldType(formFieldType),
      enum: showFormFieldSelectTextField
        ? formFieldSelectOptions.split(',')
        : undefined,
    };

    setFormFieldIdHasBeenUpdatedByUser(false);
    setShowNewFormField(false);
    setFormFields([...formFields, newFormField]);
  };

  const handleFormFieldTypeChange = (event: any) => {
    setFormFieldType(event.srcElement.value);

    if (event.srcElement.value === 'select') {
      setShowFormFieldSelectTextField(true);
    } else {
      setShowFormFieldSelectTextField(false);
    }
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
          <Select
            id="form-field-type"
            labelText="Type"
            onChange={handleFormFieldTypeChange}
          >
            {formFieldTypes.map((fft: string) => {
              return <SelectItem text={fft} value={fft} />;
            })}
          </Select>
          {showFormFieldSelectTextField ? (
            <TextInput
              id="json-form-field-select-options"
              name="select-options"
              labelText="Select Options"
              onChange={(event: any) => {
                setFormFieldSelectOptions(event.srcElement.value);
              }}
            />
          ) : null}
          <Button onClick={addFormField}>Add Field</Button>
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

  const handleSaveCallback = () => {
    setSavedJsonSchema(true);
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
    setSavedJsonSchema(false);
    let formJsonFileName = `${formId}-schema.json`;
    let formUiJsonFileName: string | null = `${formId}-uischema.json`;
    if (searchParams.get('file_name')) {
      formJsonFileName = searchParams.get('file_name') as any;
      if (formJsonFileName.match(/-schema\.json$/)) {
        formUiJsonFileName = (searchParams.get('file_name') as any).replace(
          '-schema.json',
          '-uischema.json'
        );
      } else {
        formUiJsonFileName = null;
      }
    }

    uploadFile(new File([renderFormJson()], formJsonFileName));
    if (formUiJsonFileName) {
      uploadFile(new File([renderFormUiJson()], formUiJsonFileName));
    }
  };

  const deleteFile = () => {
    const url = `/process-models/${modifiedProcessModelId}/files/${params.file_name}`;
    const httpMethod = 'DELETE';

    const navigateToProcessModelShow = (_httpResult: any) => {
      navigate(`/admin/process-models/${modifiedProcessModelId}`);
    };

    HttpService.makeCallToBackend({
      path: url,
      successCallback: navigateToProcessModelShow,
      httpMethod,
    });
  };

  const formIdTextField = () => {
    if (searchParams.get('file_name')) {
      return null;
    }
    return (
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
    );
  };

  const jsonFormButton = () => {
    if (!searchParams.get('file_name')) {
      return null;
    }
    return (
      <>
        <ButtonWithConfirmation
          data-qa="delete-process-model-file"
          description={`Delete file ${searchParams.get('file_name')}?`}
          onConfirmation={deleteFile}
          buttonLabel="Delete"
        />
        <Button
          onClick={() =>
            navigate(
              `/admin/process-models/${
                params.process_model_id
              }/form/${searchParams.get('file_name')}`
            )
          }
          variant="danger"
          data-qa="form-builder-button"
        >
          View Json
        </Button>
      </>
    );
  };
  const processModelFileName = searchParams.get('file_name') || '';

  const topOfPageElements = () => {
    return (
      <>
        <ProcessBreadcrumb
          hotCrumbs={[
            ['Process Groups', '/admin'],
            {
              entityToExplode: params.process_model_id || '',
              entityType: 'process-model-id',
              linkLastItem: true,
            },
            [processModelFileName],
          ]}
        />
        <h1>
          Process Model File{processModelFileName ? ': ' : ''}
          {processModelFileName}
        </h1>
      </>
    );
  };

  const jsonFormArea = () => {
    return (
      <>
        {formSubmitResultElement()}
        <Button onClick={saveFile}>Save</Button>
        {jsonFormButton()}
        <TextInput
          id="json-form-title"
          name="title"
          labelText="Title"
          value={formTitle}
          onChange={(event: any) => {
            onFormTitleChange(event.srcElement.value);
          }}
        />
        {formIdTextField()}
        <TextArea
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
            setFormFieldType('');
            setFormFieldSelectOptions('');
            setShowFormFieldSelectTextField(false);
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
  const schemaString = renderFormJson();
  const uiSchemaString = renderFormUiJson();
  const schema = JSON.parse(schemaString);
  const uiSchema = JSON.parse(uiSchemaString);

  return (
    <>
      {topOfPageElements()}
      <Grid fullWidth>
        <Column md={5} lg={8} sm={4}>
          {jsonFormArea()}
        </Column>
        <Column md={5} lg={8} sm={4}>
          <h2>Form Preview</h2>
          <Form
            formData={{}}
            schema={schema}
            uiSchema={uiSchema}
            validator={validator}
          />
        </Column>
      </Grid>
    </>
  );
}
