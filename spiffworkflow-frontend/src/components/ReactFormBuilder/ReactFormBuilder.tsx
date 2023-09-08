import React, { useCallback, useEffect, useState } from 'react';
import Editor from '@monaco-editor/react';
// eslint-disable-next-line import/no-extraneous-dependencies
import merge from 'lodash/merge';

import {
  Column,
  Grid,
  TabList,
  Tab,
  TabPanels,
  TabPanel,
  Tabs,
  TextInput,
  Button,
  Loading,
} from '@carbon/react';
import { useDebounce } from 'use-debounce';
import HttpService from '../../services/HttpService';
import ExamplesTable from './ExamplesTable';
import CustomForm from '../CustomForm';
import ErrorBoundary from '../ErrorBoundary';

type OwnProps = {
  processModelId: string;
  fileName: string;
  onFileNameSet: (fileName: string) => void;
};

export default function ReactFormBuilder({
  processModelId,
  fileName,
  onFileNameSet,
}: OwnProps) {
  const SCHEMA_EXTENSION = '-schema.json';
  const UI_EXTENSION = '-uischema.json';
  const DATA_EXTENSION = '-exampledata.json';

  const [fetchFailed, setFetchFailed] = useState<boolean>(false);

  const [strSchema, setStrSchema] = useState<string>('');
  const [debouncedStrSchema] = useDebounce(strSchema, 500);
  const [strUI, setStrUI] = useState<string>('');
  const [debouncedStrUI] = useDebounce(strUI, 500);
  const [strFormData, setStrFormData] = useState<string>('');
  const [debouncedFormData] = useDebounce(strFormData, 500);

  const [postJsonSchema, setPostJsonSchema] = useState<object>({});
  const [postJsonUI, setPostJsonUI] = useState<object>({});
  const [formData, setFormData] = useState<object>({});

  const [selectedIndex, setSelectedIndex] = useState(0);

  const [errorMessage, setErrorMessage] = useState<string>('');
  const [baseFileName, setBaseFileName] = useState<string>('');
  const [newFileName, setNewFileName] = useState<string>('');

  const saveFile = useCallback(
    (file: File, create: boolean = false) => {
      let httpMethod = 'PUT';
      let url = `/process-models/${processModelId}/files`;
      if (create) {
        httpMethod = 'POST';
      } else {
        url += `/${file.name}`;
      }
      const submission = new FormData();
      submission.append('file', file);
      submission.append('fileName', file.name);

      HttpService.makeCallToBackend({
        path: url,
        successCallback: () => {},
        failureCallback: () => {}, // fixme: handle errors
        httpMethod,
        postBody: submission,
      });
    },
    [processModelId]
  );

  const createFiles = (base: string) => {
    saveFile(new File(['{}'], base + SCHEMA_EXTENSION), true);
    saveFile(new File(['{}'], base + UI_EXTENSION), true);
    saveFile(new File(['{}'], base + DATA_EXTENSION), true);
    setBaseFileName(base);
    onFileNameSet(base + SCHEMA_EXTENSION);
  };

  const isReady = () => {
    return strSchema !== '' && strUI !== '' && strFormData !== '';
  };

  // Auto save schema changes
  useEffect(() => {
    if (baseFileName !== '') {
      saveFile(new File([debouncedStrSchema], baseFileName + SCHEMA_EXTENSION));
    }
  }, [debouncedStrSchema, baseFileName, saveFile]);

  // Auto save ui changes
  useEffect(() => {
    if (baseFileName !== '') {
      saveFile(new File([debouncedStrUI], baseFileName + UI_EXTENSION));
    }
  }, [debouncedStrUI, baseFileName, saveFile]);

  // Auto save example data changes
  useEffect(() => {
    if (baseFileName !== '') {
      saveFile(new File([debouncedFormData], baseFileName + DATA_EXTENSION));
    }
  }, [debouncedFormData, baseFileName, saveFile]);

  useEffect(() => {
    /**
     * we need to run the schema and ui through a backend call before rendering the form
     * so it can handle certain server side changes, such as jinja rendering and populating dropdowns, etc.
     */
    const url: string = '/tasks/prepare-form';
    let schema = {};
    let ui = {};
    let data = {};

    if (
      debouncedFormData === '' ||
      debouncedStrSchema === '' ||
      debouncedStrUI === ''
    ) {
      return;
    }

    try {
      schema = JSON.parse(debouncedStrSchema);
    } catch (e) {
      setErrorMessage('Please check the Json Schema for errors.');
      return;
    }
    try {
      ui = JSON.parse(debouncedStrUI);
    } catch (e) {
      setErrorMessage('Please check the UI Settings for errors.');
      return;
    }
    try {
      data = JSON.parse(debouncedFormData);
    } catch (e) {
      setErrorMessage('Please check the Task Data for errors.');
      return;
    }
    setErrorMessage('');

    HttpService.makeCallToBackend({
      path: url,
      successCallback: (response: any) => {
        setPostJsonSchema(response.form_schema);
        setPostJsonUI(response.form_ui);
        setErrorMessage('');
      },
      failureCallback: (error: any) => {
        setErrorMessage(error.message);
      }, // fixme: handle errors
      httpMethod: 'POST',
      postBody: {
        form_schema: schema,
        form_ui: ui,
        task_data: data,
      },
    });
  }, [debouncedStrSchema, debouncedStrUI, debouncedFormData]);

  const handleTabChange = (evt: any) => {
    setSelectedIndex(evt.selectedIndex);
  };

  function setJsonSchemaFromResponseJson(result: any) {
    setStrSchema(result.file_contents);
  }

  function setJsonUiFromResponseJson(result: any) {
    setStrUI(result.file_contents);
  }

  function setDataFromResponseJson(result: any) {
    setStrFormData(result.file_contents);
    try {
      setFormData(JSON.parse(result.file_contents));
    } catch (e) {
      // todo: show error message
      console.log('Error parsing JSON:', e);
    }
  }

  function baseName(myFileName: string): string {
    return myFileName.replace(SCHEMA_EXTENSION, '').replace(UI_EXTENSION, '');
  }

  function fetchSchema() {
    HttpService.makeCallToBackend({
      path: `/process-models/${processModelId}/files/${baseName(
        fileName
      )}${SCHEMA_EXTENSION}`,
      successCallback: (response: any) => {
        setJsonSchemaFromResponseJson(response);
        setBaseFileName(baseName(fileName));
      },
      failureCallback: () => {
        setFetchFailed(true);
      },
    });
  }

  function fetchUI() {
    HttpService.makeCallToBackend({
      path: `/process-models/${processModelId}/files/${baseName(
        fileName
      )}${UI_EXTENSION}`,
      successCallback: setJsonUiFromResponseJson,
      failureCallback: () => {},
    });
  }

  function fetchExampleData() {
    HttpService.makeCallToBackend({
      path: `/process-models/${processModelId}/files/${baseName(
        fileName
      )}${DATA_EXTENSION}`,
      successCallback: setDataFromResponseJson,
      failureCallback: () => {},
    });
  }

  function insertFields(schema: any, ui: any, data: any) {
    setFormData(merge(formData, data));
    setStrFormData(JSON.stringify(formData, null, 2));

    const tempSchema = merge(JSON.parse(strSchema), schema);
    setStrSchema(JSON.stringify(tempSchema, null, 2));

    const tempUI = merge(JSON.parse(strUI), ui);
    setStrUI(JSON.stringify(tempUI, null, 2));
  }

  function updateData(newData: object) {
    setFormData(newData);
    const newDataStr = JSON.stringify(newData, null, 2);
    if (newDataStr !== strFormData) {
      setStrFormData(newDataStr);
    }
  }
  function updateDataFromStr(newDataStr: string) {
    try {
      const newData = JSON.parse(newDataStr);
      setFormData(newData);
    } catch (e) {
      /* empty */
    }
  }

  if (!isReady()) {
    if (fileName !== '' && !fetchFailed) {
      fetchExampleData();
      fetchUI();
      fetchSchema();
      return (
        <div style={{ height: 200 }}>
          <Loading />
        </div>
      );
    }
    return (
      <Grid fullWidth>
        <Column sm={4} md={5} lg={8}>
          <h2>Schema Name</h2>
          <p>
            Please provide a name for the Schema/Web Form you are about to
            create...
          </p>
          <TextInput
            id="file_name"
            labelText="Name:"
            value={newFileName}
            onChange={(event: any) => {
              setNewFileName(event.srcElement.value);
            }}
            size="sm"
          />
          <p>The changes you make here will be automatically saved saved to:</p>
          <ul>
            <li>
              {newFileName}
              {SCHEMA_EXTENSION} (for the schema)
            </li>
            <li>
              {newFileName}
              {UI_EXTENSION} (for additional UI form settings)
            </li>
            <li>
              {newFileName}
              {DATA_EXTENSION} (for example data to test the form
            </li>
          </ul>
          <Button
            className="react-json-schema-form-submit-button"
            type="submit"
            onClick={() => {
              createFiles(newFileName);
            }}
          >
            Create Files
          </Button>
        </Column>
      </Grid>
    );
  }
  return (
    <Grid fullWidth>
      <Column sm={4} md={5} lg={8}>
        <Tabs selectedIndex={selectedIndex} onChange={handleTabChange}>
          <TabList aria-label="Editor Options">
            <Tab>Json Schema</Tab>
            <Tab>UI Settings</Tab>
            <Tab>Data View</Tab>
            <Tab>Examples</Tab>
          </TabList>
          <TabPanels>
            <TabPanel>
              <p>
                The Json Schema describes the structure of the data you want to
                collect, and what validation rules should be applied to each
                field.
                <a
                  target="new"
                  href="https://json-schema.org/learn/getting-started-step-by-step"
                >
                  Read More
                </a>
              </p>
              <Editor
                height={600}
                width="auto"
                defaultLanguage="json"
                value={strSchema}
                onChange={(value) => setStrSchema(value || '')}
              />
            </TabPanel>
            <TabPanel>
              <p>
                These UI Settings augment the Json Schema, specifying how the
                web form should be displayed.
                <a
                  target="new"
                  href="https://rjsf-team.github.io/react-jsonschema-form/docs/"
                >
                  Learn More.
                </a>
              </p>
              <Editor
                height={600}
                width="auto"
                defaultLanguage="json"
                value={strUI}
                onChange={(value) => setStrUI(value || '')}
              />
            </TabPanel>
            <TabPanel>
              <p>
                Data entered in the form to the right will appear below in the
                same way it will be provided in the Task Data.
              </p>
              <Editor
                height={600}
                width="auto"
                defaultLanguage="json"
                value={strFormData}
                onChange={(value: any) => updateDataFromStr(value || '')}
              />
            </TabPanel>
            <TabPanel>
              <p>
                If you are looking for a place to start, try adding these
                example fields to your form and changing them to meet your
                needs.
              </p>
              <ExamplesTable onSelect={insertFields} />
            </TabPanel>
          </TabPanels>
        </Tabs>
      </Column>
      <Column sm={4} md={5} lg={8}>
        <h2>Form Preview</h2>
        <div>{errorMessage}</div>
        <ErrorBoundary>
          <CustomForm
            id="custom_form"
            formData={formData}
            onChange={(e: any) => updateData(e.formData)}
            schema={postJsonSchema}
            uiSchema={postJsonUI}
          />
        </ErrorBoundary>
      </Column>
    </Grid>
  );
}
