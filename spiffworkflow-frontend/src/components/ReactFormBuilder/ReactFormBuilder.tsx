import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import { Column, Grid, TabList, Tab, TabPanels, TabPanel } from '@carbon/react';
import validator from '@rjsf/validator-ajv8';
import { Form } from '../../rjsf/carbon_theme';
import HttpService from '../../services/HttpService';
import ExamplesTable from './ExamplesTable';

type OwnProps = {
  processModelId: string;
  fileName: string;
};

export default function ReactFormBuilder({
  processModelId,
  fileName,
}: OwnProps) {
  const [strSchema, setStrSchema] = useState<string>('');
  const [strUI, setStrUI] = useState<string>('');
  const [jsonSchema, setJsonSchema] = useState<object>({});
  const [jsonUI, setJsonUI] = useState<object>({});

  function setJsonSchemaFromResponseJson(result: any) {
    setStrSchema(result.file_contents);
    setJsonSchema(JSON.parse(result.file_contents));
    console.log('Json Schema:', result.file_contents);
  }

  function setJsonUiFromResponseJson(result: any) {
    setStrUI(result.file_contents);
    setJsonUI(JSON.parse(result.file_contents));
    console.log('Json UI:', result.file_contents);
  }

  function fetchSchema() {
    HttpService.makeCallToBackend({
      path: `/process-models/${processModelId}/files/${fileName}`,
      successCallback: setJsonSchemaFromResponseJson,
    });
  }

  function fetchSchemaUI() {
    HttpService.makeCallToBackend({
      path: `/process-models/${processModelId}/files/${fileName}`,
      successCallback: setJsonUiFromResponseJson,
    });
  }

  // Load the schema and ui schema from the server
  if (fileName !== '') {
    fetchSchema();
    fetchSchemaUI();
  }

  function update(schema: object, ui: object) {
    setJsonSchema(schema);
    setJsonUI(ui);
    setStrSchema(JSON.stringify(schema, null, 2));
    setStrUI(JSON.stringify(ui, null, 2));
  }

  return (
    <Grid fullWidth>
      <Column md={5} lg={8} sm={4}>
        <TabList aria-label="Editor Options">
          <Tab>Select Pre-Built</Tab>
          <Tab>JSON Editor</Tab>
          <Tab>Form Builder</Tab>
          <Tab>AI Generator</Tab>
        </TabList>
        <TabPanels>
          <TabPanel>
            <ExamplesTable onSelect={update} />
          </TabPanel>
          <TabPanel>
            <Editor
              height={600}
              width="auto"
              defaultLanguage="json"
              defaultValue={strSchema}
              onChange={(value) => setStrSchema(value || '')}
            />
          </TabPanel>
        </TabPanels>
      </Column>
      <Column md={5} lg={8} sm={4}>
        <h2>Form Preview</h2>
        <Form
          formData={{}}
          schema={jsonSchema}
          uiSchema={jsonUI}
          validator={validator}
        />
      </Column>
    </Grid>
  );
}
