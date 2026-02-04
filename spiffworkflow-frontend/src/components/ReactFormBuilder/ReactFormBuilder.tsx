import React, { useEffect, useState, useRef } from 'react';
import { useTranslation } from 'react-i18next';

import { Editor, loader } from '@monaco-editor/react';
import * as monaco from 'monaco-editor';

import merge from 'lodash/merge';

import {
  TextField,
  Button,
  CircularProgress,
  Tabs,
  Tab,
  Box,
  Typography,
} from '@mui/material';
import Grid from '@mui/material/Grid';
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
  const { t } = useTranslation();

  return (
    <Notification
      title={t('form_render_error_title')}
      onClose={() => resetBoundary()}
      type="error"
    >
      <p>{t('form_render_error_message')}</p>
      <p>{error.message}</p>
      <Button onClick={resetBoundary}>{t('try_again')}</Button>
    </Notification>
  );
}

type OwnProps = {
  modifiedProcessModelId: string;
  fileName: string;
  onFileNameSet: (fileName: string) => void;
  canCreateFiles: boolean;
  canUpdateFiles: boolean;
  pythonWorker: any;
};

export default function ReactFormBuilder({
  modifiedProcessModelId,
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

  const { t } = useTranslation();
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

    pythonWorker.onmessage = async (error: any) => {
      if (error.data.type !== 'didJinjaForm') {
        console.log('unknown python worker response: ', error);
        return;
      }

      if (error.data.err) {
        setErrorMessage(error.data.err);
        return;
      }

      try {
        const schema = JSON.parse(error.data.strSchema);
        setPostJsonSchema(schema);
      } catch (e) {
        setErrorMessage('Please check the Json Schema for errors.');
        return;
      }
      try {
        const ui = JSON.parse(error.data.strUI);
        setPostJsonUI(ui);
      } catch (e) {
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
    let url = `/process-models/${modifiedProcessModelId}/files`;
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
        setErrorMessage(t('file_save_error', { fileName, error: e.message }));
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

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
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
      path: `/process-models/${modifiedProcessModelId}/files/${baseName(
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
      path: `/process-models/${modifiedProcessModelId}/files/${baseName(
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
      path: `/process-models/${modifiedProcessModelId}/files/${baseName(
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
        <Grid size={{ xs: 12 }}>
          <Typography variant="h4">{t('schema_name')}</Typography>
          <Typography variant="body1">{t('provide_schema_name')}</Typography>
          <TextField
            id="file_name"
            label={t('name')}
            error={filenameBaseInvalid}
            helperText={
              filenameBaseInvalid ? t('schema_name_requirements') : ''
            }
            value={newFileName}
            onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
              setNewFileName(event.target.value);
            }}
            size="small"
          />
          <Typography variant="body1">{t('auto_save_notice')}</Typography>
          <ul>
            <li>
              {newFileName}
              {SCHEMA_EXTENSION} {t('for_schema')}
            </li>
            <li>
              {newFileName}
              {UI_EXTENSION} {t('for_ui_settings')}
            </li>
            <li>
              {newFileName}
              {DATA_EXTENSION} {t('for_example_data')}
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
              {t('create_files')}
            </Button>
          ) : null}
        </Grid>
      </Grid>
    );
  }
  return (
    <Grid container spacing={3}>
      <Grid size={{ xs: 12, md: 6 }}>
        <Tabs value={selectedIndex} onChange={handleTabChange}>
          <Tab label={t('json_schema')} />
          <Tab label={t('ui_settings')} />
          <Tab label={t('data_view')} />
          {canUpdateFiles ? <Tab label={t('examples')} /> : null}
        </Tabs>
        <Box>
          {selectedIndex === 0 && (
            <Box>
              <Typography variant="body1">
                {t('json_schema_description')}{' '}
                <a
                  target="_spiff_rjsf_read_me"
                  href="https://json-schema.org/learn/getting-started-step-by-step"
                >
                  {t('read_more')}
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
                {t('ui_settings_description')}{' '}
                <a
                  target="_spiff_rjsf_learn_more"
                  href="https://rjsf-team.github.io/react-jsonschema-form/docs/"
                >
                  {t('learn_more')}
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
                {t('data_view_description')}
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
                {t('examples_description')}
              </Typography>
              <ExamplesTable onSelect={insertFields} />
            </Box>
          )}
        </Box>
      </Grid>
      <Grid size={{ xs: 12, md: 6 }}>
        <Typography variant="h4">{t('form_preview')}</Typography>
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
