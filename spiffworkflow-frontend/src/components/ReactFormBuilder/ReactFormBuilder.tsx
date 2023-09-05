import React, { useCallback, useEffect, useState } from 'react';
import Editor from '@monaco-editor/react';

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
import validator from '@rjsf/validator-ajv8';
import { useDebounce } from 'use-debounce';
import { Form } from '../../rjsf/carbon_theme';
import HttpService from '../../services/HttpService';
import ExamplesTable from './ExamplesTable';

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

  const [ready, setReady] = useState<boolean>(false);
  const [fetchFailed, setFetchFailed] = useState<boolean>(false);

  const [strSchema, setStrSchema] = useState<string>('{}');
  const [debouncedStrSchema] = useDebounce(strSchema, 500);
  const [strUI, setStrUI] = useState<string>('{}');
  const [debouncedStrUI] = useDebounce(strUI, 500);
  const [jsonSchema, setJsonSchema] = useState<object>({});
  const [jsonUI, setJsonUI] = useState<object>({});
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [formData, setFormData] = useState<object>({});
  const [strFormData, setStrFormData] = useState<string>('{}');

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
        successCallback: () => {
          setReady(true);
        },
        failureCallback: () => {}, // fixme: handle errors
        httpMethod,
        postBody: submission,
      });
    },
    [processModelId]
  );

  const getSchemaFile = (base: string): File => {
    return new File([debouncedStrSchema], base + SCHEMA_EXTENSION);
  };

  const getUIFile = (base: string): File => {
    return new File([debouncedStrUI], base + UI_EXTENSION);
  };

  const createFiles = (base: string) => {
    saveFile(getSchemaFile(base), true);
    saveFile(getUIFile(base), true);
    setBaseFileName(base);
    onFileNameSet(getSchemaFile(base).name);
  };

  // Auto save schema changes
  useEffect(() => {
    if (baseFileName !== '') {
      saveFile(getSchemaFile(baseFileName));
    }
  }, [debouncedStrSchema, baseFileName, saveFile]);

  // Auto save ui changes
  useEffect(() => {
    if (baseFileName !== '') {
      saveFile(getUIFile(baseFileName));
    }
  }, [debouncedStrUI, baseFileName, saveFile]);

  const handleTabChange = (evt: any) => {
    setSelectedIndex(evt.selectedIndex);
  };

  function setJsonSchemaFromResponseJson(result: any) {
    setStrSchema(result.file_contents);
    try {
      setJsonSchema(JSON.parse(result.file_contents));
      setReady(true);
    } catch (e) {
      // todo: show error message
      console.log('Error parsing JSON:', e);
    }
    3;
  }

  function setJsonUiFromResponseJson(result: any) {
    setStrUI(result.file_contents);
    try {
      setJsonUI(JSON.parse(result.file_contents));
    } catch (e) {
      // todo: show error message
      console.log('Error parsing JSON:', e);
    }
    console.log('Json UI:', result.file_contents);
  }

  function baseName(myFileName: string): string {
    return myFileName.replace(SCHEMA_EXTENSION, '').replace(UI_EXTENSION, '');
  }

  function fetchSchema() {
    HttpService.makeCallToBackend({
      path: `/process-models/${processModelId}/files/${baseName(
        fileName
      )}${SCHEMA_EXTENSION}`,
      successCallback: setJsonSchemaFromResponseJson,
      failureCallback: () => {
        setReady(false);
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

  function update(schema: object, ui: object) {
    setJsonSchema(schema);
    setJsonUI(ui);
    setStrSchema(JSON.stringify(schema, null, 2));
    setStrUI(JSON.stringify(ui, null, 2));
  }

  function updateSchemaString(newSchema: string) {
    setStrSchema(newSchema);
    try {
      setJsonSchema(JSON.parse(newSchema));
    } catch (e) {
      // todo: show error message
    }
  }

  function updateUIString(newUI: string) {
    setStrUI(newUI);
    try {
      setJsonUI(JSON.parse(newUI));
    } catch (e) {
      // todo: show error message
    }
  }

  function updateDataString(newData: string) {
    console.log('Seting data string');
    setStrFormData(newData);
    try {
      setFormData(JSON.parse(newData));
    } catch (e) {
      // todo: show error message
    }
  }

  function updateData(newData: object) {
    console.log('Seting data string');
    setFormData(newData);
    setStrFormData(JSON.stringify(newData, null, 2));
  }

  if (!ready) {
    if (fileName !== '' && !fetchFailed) {
      fetchSchema();
      fetchUI();
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
                field.&nbps;
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
                onChange={(value) => updateSchemaString(value || '')}
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
                onChange={(value) => updateUIString(value || '')}
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
                onChange={(value: any) => updateDataString(value || '{}')}
              />
            </TabPanel>
            <TabPanel>
              <ExamplesTable onSelect={update} />
            </TabPanel>
          </TabPanels>
        </Tabs>
      </Column>
      <Column sm={4} md={5} lg={8}>
        <h2>Form Preview</h2>
        <Form
          formData={formData}
          onChange={(e) => updateData(e.formData)}
          schema={jsonSchema}
          uiSchema={jsonUI}
          validator={validator}
        />
      </Column>
    </Grid>
  );
}
