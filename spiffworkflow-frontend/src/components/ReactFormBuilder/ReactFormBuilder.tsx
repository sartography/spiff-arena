import React, { useEffect, useState, useRef } from 'react';

import Editor, { loader } from '@monaco-editor/react';
import * as monaco from 'monaco-editor';

// @ts-ignore
// eslint-disable-next-line import/no-extraneous-dependencies
import merge from 'lodash/merge';

import {
  Grid,
  TextField,
  Button,
  CircularProgress,
  Tabs,
  Tab,
  Box,
  Typography,
} from '@mui/material';
import { useDebouncedCallback } from 'use-debounce';
import { ErrorBoundary, useErrorBoundary } from 'react-error-boundary';
import HttpService from '../../services/HttpService';
import ExamplesTable from './ExamplesTable';
import CustomForm from '../CustomForm';
import { Notification } from '../Notification';

loader.config({ monaco });

type ErrorProps = {
  error: Error;
};

function FormErrorFallback({ error }: ErrorProps) {
  // This is displayed if the ErrorBoundary catches an error when rendering the form.
  const { resetBoundary } = useErrorBoundary();

  return (
    <Notification
      title="Failed to render form. "
      onClose={() => resetBoundary()}
      type="error"
    >
      <p>
        The form could not be built with the current schema, UI and data. Please
        try to correct the issue and try again.
      </p>
      <p>{error.message}</p>
      <Button onClick={resetBoundary}>Try again</Button>
    </Notification>
  );
}

type OwnProps = {
  processModelId: string;
  fileName: string;
  onFileNameSet: (fileName: string) => void;
  canCreateFiles: boolean;
  canUpdateFiles: boolean;
  pythonWorker: any;
};

export default function ReactFormBuilder({
  processModelId,
  fileName,
  onFileNameSet,
  canCreateFiles,
  canUpdateFiles,
  pythonWorker,
}: OwnProps) {
  const SCHEMA_EXTENSION = '-schema.json';
  const UI_EXTENSION = '-uischema.json';
  const DATA_EXTENSION = '-exampledata.json';

  const [fetchFailed, setFetchFailed] = useState<boolean>(false);
  const [ready, setReady] = useState<boolean>(false);

  const [filenameBaseInvalid, setFilenameBaseInvalid] =
    useState<boolean>(false);

  const [strSchema, setStrSchema] = useState<string>('');
  const [strUI, setStrUI] = useState<string>('');
  const [strFormData, setStrFormData] = useState<string>('');

  const [postJsonSchema, setPostJsonSchema] = useState<object>({});
  const [postJsonUI, setPostJsonUI] = useState<object>({});
  const [formData, setFormData] = useState<object>({});

  const [selectedIndex, setSelectedIndex] = useState(0);

  const [errorMessage, setErrorMessage] = useState<string>('');
  const [baseFileName, setBaseFileName] = useState<string>('');
  const [newFileName, setNewFileName] = useState<string>('');

  /**
   * This section gives us direct pointers to the monoco editors so that
   * we can update their values.  Using state variables directly on the monoco editor
   * causes the cursor to jump to the bottom if two letters are pressed simultaneously.
   */
  const schemaEditorRef = useRef(null);
  const uiEditorRef = useRef(null);
  const dataEditorRef = useRef(null);
  function handleSchemaEditorDidMount(editor: any) {
    schemaEditorRef.current = editor;
  }
  function handleUiEditorDidMount(editor: any) {
    uiEditorRef.current = editor;
  }
  function handleDataEditorDidMount(editor: any) {
    dataEditorRef.current = editor;
  }

  useEffect(() => {
    if (pythonWorker === null) {
      return;
    }

    // TODO: when we use this in more than one place we will need a better dispatching mechanism
    // eslint-disable-next-line no-param-reassign
    pythonWorker.onmessage = async (e: any) => {
      if (e.data.type !== 'didJinjaForm') {
        console.log('unknown python worker response: ', e);
        return;
      }

      if (e.data.err) {
        setErrorMessage(e.data.err);
        return;
      }

      try {
        const schema = JSON.parse(e.data.strSchema);
        setPostJsonSchema(schema);
      } catch (err) {
        setErrorMessage('Please check the Json Schema for errors.');
        return;
      }
      try {
        const ui = JSON.parse(e.data.strUI);
        setPostJsonUI(ui);
      } catch (err) {
        setErrorMessage('Please check the UI Settings for errors.');
        return;
      }

      setErrorMessage('');
    };
  }, [pythonWorker]);

  useEffect(() => {
    /**
     * we need to run the schema and ui through the python web worker before rendering the form,
     * so it can mimic certain server side changes, such as jinja rendering and populating dropdowns, etc.
     */
    if (strSchema === '' || strUI === '' || strFormData === '') {
      return;
    }

    setErrorMessage('');

    try {
      JSON.parse(strFormData);
    } catch (e) {
      setErrorMessage('Please check the Data View for errors.');
      return;
    }

    pythonWorker.postMessage({
      type: 'jinjaForm',
      strSchema,
      strUI,
      strFormData,
    });
  }, [strSchema, strUI, strFormData, canCreateFiles, pythonWorker]);

  const saveFile = (
    file: File,
    create: boolean = false,
    callback: Function | null = null,
  ) => {
    if ((create && !canCreateFiles) || (!create && !canUpdateFiles)) {
      return;
    }
    let httpMethod = 'PUT';
    let url = `/process-models/${processModelId}/files`;
    if (create && canCreateFiles) {
      httpMethod = 'POST';
    } else if (canUpdateFiles) {
      url += `/${file.name}`;
    }

    const submission = new FormData();
    submission.append('file', file);
    submission.append('fileName', file.name);

    HttpService.makeCallToBackend({
      path: url,
      successCallback: () => {
        if (callback) {
          callback();
        }
      },
      failureCallback: (e: any) => {
        setErrorMessage(`Failed to save file: '${fileName}'. ${e.message}`);
      },
      httpMethod,
      postBody: submission,
    });
  };

  const hasValidName = (identifierToCheck: string) => {
    return identifierToCheck.match(/^[a-z0-9][0-9a-z-]+[a-z0-9]$/);
  };

  const createFiles = (base: string) => {
    if (hasValidName(base)) {
      // meaning it switched from invalid to valid
      if (filenameBaseInvalid) {
        setFilenameBaseInvalid(false);
      }
    } else {
      setFilenameBaseInvalid(true);
      return;
    }
    saveFile(new File(['{}'], base + SCHEMA_EXTENSION), true, () => {
      saveFile(new File(['{}'], base + UI_EXTENSION), true, () => {
        saveFile(new File(['{}'], base + DATA_EXTENSION), true, () => {
          setBaseFileName(base);
          onFileNameSet(base + SCHEMA_EXTENSION);
          setStrSchema('{}');
          setStrUI('{}');
          setStrFormData('{}');
        });
      });
    });
  };

  const isReady = () => {
    // Use a ready flag so that we still allow people to completely delete
    // the schema, ui or data if they want to clear it out.
    if (ready) {
      return true;
    }
    if (strSchema !== '' && strUI !== '' && strFormData !== '') {
      setReady(true);
      return true;
    }
    return false;
  };

  // if we share a debounce and update all str states at once
  // then only one will get fired so split them out like this.
  const updateStrFileDebounce = useDebouncedCallback((newContent: string) => {
    saveFile(new File([newContent], baseFileName + SCHEMA_EXTENSION));
  }, 500);
  const updateStrUIFileDebounce = useDebouncedCallback((newContent: string) => {
    saveFile(new File([newContent], baseFileName + UI_EXTENSION));
  }, 500);
  const updateFormDataFileDebounce = useDebouncedCallback(
    (newContent: string) => {
      saveFile(new File([newContent], baseFileName + DATA_EXTENSION));
    },
    500,
  );

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setSelectedIndex(newValue);
  };

  const updateStrSchema = (value: string) => {
    updateStrFileDebounce(value);
    setStrSchema(value);
  };

  const updateStrUi = (value: string) => {
    updateStrUIFileDebounce(value);
    setStrUI(value);
  };

  const updateStrData = (value: string) => {
    updateFormDataFileDebounce(value);
    setStrFormData(value);
  };

  function updateData(newData: object) {
    setFormData(newData);
    const newDataStr = JSON.stringify(newData, null, 2);
    if (newDataStr !== strFormData) {
      updateStrData(newDataStr);
    }
  }

  function updateDataFromStr(newDataStr: string) {
    try {
      setStrFormData(newDataStr);
      const newData = JSON.parse(newDataStr);
      setFormData(newData);
    } catch (e) {
      /* empty */
    }
  }

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
      console.error('Error parsing JSON:', e);
    }
  }

  function baseName(myFileName: string): string {
    return myFileName.replace(SCHEMA_EXTENSION, '').replace(UI_EXTENSION, '');
  }

  function fetchSchema() {
    HttpService.makeCallToBackend({
      path: `/process-models/${processModelId}/files/${baseName(
        fileName,
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
        fileName,
      )}${UI_EXTENSION}`,
      successCallback: setJsonUiFromResponseJson,
      failureCallback: () => {
        setJsonUiFromResponseJson({ file_contents: '{}' });
      },
    });
  }

  function fetchExampleData() {
    HttpService.makeCallToBackend({
      path: `/process-models/${processModelId}/files/${baseName(
        fileName,
      )}${DATA_EXTENSION}`,
      successCallback: setDataFromResponseJson,
      failureCallback: () => {
        setDataFromResponseJson({ file_contents: '{}' });
      },
    });
  }

  function insertFields(schema: any, ui: any, data: any) {
    setFormData(merge(formData, data));
    updateStrData(JSON.stringify(formData, null, 2));

    const tempSchema = merge(JSON.parse(strSchema), schema);
    updateStrSchema(JSON.stringify(tempSchema, null, 2));

    const tempUI = merge(JSON.parse(strUI), ui);
    updateStrUi(JSON.stringify(tempUI, null, 2));
  }

  if (!isReady()) {
    if (fileName !== '' && !fetchFailed) {
      fetchExampleData();
      fetchUI();
      fetchSchema();
      return (
        <div style={{ height: 200 }}>
          <CircularProgress />
        </div>
      );
    }
    return (
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Typography variant="h4">Schema Name</Typography>
          <Typography variant="body1">
            Please provide a name for the Schema/Web Form you are about to
            create...
          </Typography>
          <TextField
            id="file_name"
            label="Name"
            error={filenameBaseInvalid}
            helperText={
              filenameBaseInvalid
                ? 'Name is required, must be at least three characters, and must be all lowercase characters and hyphens.'
                : ''
            }
            value={newFileName}
            onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
              setNewFileName(event.target.value);
            }}
            size="small"
          />
          <Typography variant="body1">
            The changes you make here will be automatically saved to:
          </Typography>
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
          {canCreateFiles ? (
            <Button
              className="react-json-schema-form-submit-button"
              type="submit"
              onClick={() => {
                createFiles(newFileName);
              }}
            >
              Create Files
            </Button>
          ) : null}
        </Grid>
      </Grid>
    );
  }
  return (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <Tabs value={selectedIndex} onChange={handleTabChange}>
          <Tab label="Json Schema" />
          <Tab label="UI Settings" />
          <Tab label="Data View" />
          {canUpdateFiles ? <Tab label="Examples" /> : null}
        </Tabs>
        <Box>
          {selectedIndex === 0 && (
            <Box>
              <Typography variant="body1">
                The Json Schema describes the structure of the data you want to
                collect, and what validation rules should be applied to each
                field.{' '}
                <a
                  target="_spiff_rjsf_read_me"
                  href="https://json-schema.org/learn/getting-started-step-by-step"
                >
                  Read more
                </a>
                .
              </Typography>
              <Editor
                height={600}
                width="auto"
                defaultLanguage="json"
                defaultValue={strSchema}
                onChange={(value) => {
                  updateStrFileDebounce(value || '');
                  setStrSchema(value || '');
                }}
                onMount={handleSchemaEditorDidMount}
                options={{ readOnly: !canUpdateFiles }}
              />
            </Box>
          )}
          {selectedIndex === 1 && (
            <Box>
              <Typography variant="body1">
                These UI Settings augment the Json Schema, specifying how the
                web form should be displayed.{' '}
                <a
                  target="_spiff_rjsf_learn_more"
                  href="https://rjsf-team.github.io/react-jsonschema-form/docs/"
                >
                  Learn more
                </a>
                .
              </Typography>
              <Editor
                height={600}
                width="auto"
                defaultLanguage="json"
                defaultValue={strUI}
                onChange={(value) => {
                  updateStrUIFileDebounce(value || '');
                  setStrUI(value || '');
                }}
                onMount={handleUiEditorDidMount}
                options={{ readOnly: !canUpdateFiles }}
              />
            </Box>
          )}
          {selectedIndex === 2 && (
            <Box>
              <Typography variant="body1">
                Data entered in the form to the right will appear below in the
                same way it will be provided in the Task Data. In order to
                initialize a form in the Workflow with preconfigured values or
                set up options for dynamic Dropdown lists, this data must be
                made available as Task Data variables.
              </Typography>
              <Editor
                height={600}
                width="auto"
                defaultLanguage="json"
                defaultValue={strFormData}
                onChange={(value) => {
                  updateFormDataFileDebounce(value || '');
                  updateDataFromStr(value || '');
                }}
                onMount={handleDataEditorDidMount}
                options={{ readOnly: !canUpdateFiles }}
              />
            </Box>
          )}
          {selectedIndex === 3 && canUpdateFiles && (
            <Box>
              <Typography variant="body1">
                If you are looking for a place to start, try adding these
                example fields to your form and changing them to meet your
                needs.
              </Typography>
              <ExamplesTable onSelect={insertFields} />
            </Box>
          )}
        </Box>
      </Grid>
      <Grid item xs={12} md={6}>
        <Typography variant="h4">Form Preview</Typography>
        <div className="error_info_small">{errorMessage}</div>
        <ErrorBoundary FallbackComponent={FormErrorFallback}>
          <CustomForm
            id="custom_form"
            key="custom_form"
            formData={formData}
            onChange={(e: any) => updateData(e.formData)}
            schema={postJsonSchema}
            uiSchema={postJsonUI}
          />
        </ErrorBoundary>
      </Grid>
    </Grid>
  );
}
