import {
  ReactNode,
  SyntheticEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from 'react';
import {
  generatePath,
  useNavigate,
  useParams,
  useSearchParams,
} from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Button,
  ButtonGroup,
  Dialog,
  Tabs,
  Tab,
  TextField,
  Box,
  Stack,
  TextareaAutosize,
  CircularProgress,
  IconButton,
  Tooltip,
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  SkipNext,
  SkipPrevious,
  PlayArrow,
  Close,
  Check,
  Info,
} from '@mui/icons-material';

import { Can } from '@casl/react';
import { Editor, DiffEditor } from '@monaco-editor/react';
import MDEditor from '@uiw/react-md-editor';
import HttpService from '../services/HttpService';
import ReactDiagramEditor from '../components/ReactDiagramEditor';
import ReactFormBuilder from '../components/ReactFormBuilder/ReactFormBuilder';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import useAPIError from '../hooks/UseApiError';
import {
  useBpmnEditorCallbacks,
  useBpmnEditorModals,
  useProcessReferences,
  ProcessSearch,
  useBpmnEditorTextEditorsState,
  useBpmnEditorScriptState,
  findFileNameForReferenceId,
  fireScriptUpdate,
  fireMessageSave,
  closeMarkdownEditorWithUpdate,
  closeJsonSchemaEditorWithUpdate,
  closeMessageEditorAndRefresh,
} from '../../packages/bpmn-js-spiffworkflow-react/src';
import { spiffBpmnApiService } from '../services/SpiffBpmnApiService';
import {
  getGroupFromModifiedModelId,
  makeid,
  modifyProcessIdentifierForPathParam,
  setPageTitle,
} from '../helpers';
import {
  PermissionsToCheck,
  ProcessFile,
  ProcessModel,
  ProcessReference,
} from '../interfaces';
import { Notification } from '../components/Notification';
import ActiveUsers from '../components/ActiveUsers';
import useScriptAssistEnabled from '../hooks/useScriptAssistEnabled';
import useProcessScriptAssistMessage from '../hooks/useProcessScriptAssistQuery';
import { MessageEditor } from '../components/messages/MessageEditor';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import { usePermissionFetcher } from '../hooks/PermissionService';

function TabPanel(props: {
  children?: ReactNode;
  index: number;
  value: number;
}) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function ProcessModelEditDiagram() {
  const { t } = useTranslation();
  const [showFileNameEditor, setShowFileNameEditor] = useState(false);
  const handleShowFileNameEditor = () => setShowFileNameEditor(true);
  const [processModel, setProcessModel] = useState<ProcessModel | null>(null);
  const [diagramHasChanges, setDiagramHasChanges] = useState<boolean>(false);


  const [displaySaveFileMessage, setDisplaySaveFileMessage] =
    useState<boolean>(false);
  const [processModelFileInvalidText, setProcessModelFileInvalidText] =
    useState<string>('');
  const [scriptEditorTabValue, setScriptEditorTabValue] = useState<number>(0);


  const editorRef = useRef(null);
  const monacoRef = useRef(null);

  const failingScriptLineClassNamePrefix = 'failingScriptLineError';

  const [scriptAssistValue, setScriptAssistValue] = useState<string>('');
  const [scriptAssistError, setScriptAssistError] = useState<string | null>(
    null,
  );
  const { scriptAssistEnabled } = useScriptAssistEnabled();
  const { setScriptAssistQuery, scriptAssistLoading, scriptAssistResult } =
    useProcessScriptAssistMessage();

  const { targetUris } = useUriListForPermissions();
  const permissionRequestData: PermissionsToCheck = {
    [targetUris.messageModelListPath]: ['GET'],
    [targetUris.processModelFileCreatePath]: ['PUT', 'POST'],
  };
  const { ability, permissionsLoaded } = usePermissionFetcher(
    permissionRequestData,
  );

  // Use reusable hooks from bpmn-js-spiffworkflow-react package
  const bpmnEditorCallbacks = useBpmnEditorCallbacks({
    apiService: spiffBpmnApiService,
    processModel,
    canAccessMessages: ability.can('GET', targetUris.messageModelListPath),
    messageModelListPath: targetUris.messageModelListPath,
  });
  const { onMessagesRequested } = bpmnEditorCallbacks;
  const {
    onLaunchScriptEditor,
    onLaunchMarkdownEditor,
    onLaunchMessageEditor,
    onLaunchJsonSchemaEditor: launchJsonSchemaEditor,
    onSearchProcessModels,
    scriptEditorState,
    markdownEditorState,
    messageEditorState,
    jsonSchemaEditorState,
    processSearchState,
    closeScriptEditor,
    closeMarkdownEditor,
    closeMessageEditor,
    closeJsonSchemaEditor,
    selectProcessSearchResult,
  } = useBpmnEditorModals();
  const {
    scriptText,
    setScriptText,
    scriptType,
    scriptEventBus,
    scriptElement,
    scriptModeling,
  } = useBpmnEditorScriptState({ scriptEditorState });
  const {
    markdownText,
    setMarkdownText,
    markdownEventBus,
    jsonSchemaFileName,
    setJsonSchemaFileName,
    fileEventBus,
  } = useBpmnEditorTextEditorsState({
    markdownEditorState,
    jsonSchemaEditorState,
  });

  function handleEditorDidMount(editor: any, monaco: any) {
    // here is the editor instance
    // you can store it in `useRef` for further usage
    editorRef.current = editor;
    monacoRef.current = monaco;
  }

  interface ScriptUnitTest {
    id: string;
    inputJson: any;
    expectedOutputJson: any;
  }

  interface ScriptUnitTestResult {
    result: boolean;
    context?: object;
    error?: string;
    line_number?: number;
    offset?: number;
  }

  const [currentScriptUnitTest, setCurrentScriptUnitTest] =
    useState<ScriptUnitTest | null>(null);
  const [currentScriptUnitTestIndex, setCurrentScriptUnitTestIndex] =
    useState<number>(-1);
  const [scriptUnitTestResult, setScriptUnitTestResult] =
    useState<ScriptUnitTestResult | null>(null);

  const params = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const { addError, removeError } = useAPIError();
  const [processModelFile, setProcessModelFile] = useState<ProcessFile | null>(
    null,
  );
  const [newFileName, setNewFileName] = useState('');
  const [bpmnXmlForDiagramRendering, setBpmnXmlForDiagramRendering] =
    useState(null);

  const modifiedProcessModelId = modifyProcessIdentifierForPathParam(
    (params as any).process_model_id,
  );

  const processModelPath = `process-models/${modifiedProcessModelId}`;

  const [callers, setCallers] = useState<ProcessReference[]>([]);

  const [pythonWorker, setPythonWorker] = useState<Worker | null>(null);

  const handleEditorScriptChange = (value: any) => {
    setScriptText(value);
  };

  const [{ processes }, { refresh: refreshProcesses }] = useProcessReferences({
    apiService: spiffBpmnApiService,
  });

  useEffect(() => {
    const worker = new Worker(
      new URL('/src/workers/python.ts', import.meta.url),
    );
    setPythonWorker(worker);
    return () => {
      worker.terminate();
    };
  }, []);

  useEffect(() => {
    const fileResult = (result: any) => {
      setProcessModelFile(result);
      setBpmnXmlForDiagramRendering(result.file_contents);
    };
    HttpService.makeCallToBackend({
      path: `/${processModelPath}?include_file_references=true`,
      successCallback: (result: any) => {
        setProcessModel(result);
      },
    });

    if (params.file_name) {
      HttpService.makeCallToBackend({
        path: `/${processModelPath}/files/${params.file_name}`,
        successCallback: fileResult,
      });
    }
  }, [processModelPath, params.file_name]);

  useEffect(() => {
    const bpmnProcessIds = processModelFile?.bpmn_process_ids;
    if (processModel !== null && bpmnProcessIds) {
      HttpService.makeCallToBackend({
        path: `/processes/callers/${bpmnProcessIds.join(',')}`,
        successCallback: setCallers,
      });
    }
    if (processModel && processModelFile) {
      setPageTitle([processModel.display_name, processModelFile.name]);
    }
  }, [processModel, processModelFile]);

  /**
   * When the value of the Editor is updated dynamically async,
   * it doesn't seem to fire an onChange (discussions as recent as 4.2.1).
   * The straightforward recommended fix is to handle manually, so when
   * the scriptAssistResult is updated, call the handler manually.
   */
  useEffect(() => {
    if (scriptAssistResult) {
      if (scriptAssistResult.result) {
        handleEditorScriptChange(scriptAssistResult.result);
      } else if (scriptAssistResult.error_code && scriptAssistResult.message) {
        setScriptAssistError(scriptAssistResult.message);
      } else {
        setScriptAssistError('Received unexpected response from server.');
      }
    }
  }, [scriptAssistResult]);

  const handleFileNameCancel = () => {
    setShowFileNameEditor(false);
    setNewFileName('');
    setProcessModelFileInvalidText('');
  };

  const getProcessModelSpecs = () => {
    const httpMethod = 'GET';
    const path = `/process-models/${modifiedProcessModelId}/validate`;

    HttpService.makeCallToBackend({
      path,
      httpMethod,
      failureCallback: addError,
      successCallback: (_result: any) => {},
    });
  };

  const navigateToProcessModelFile = (file: ProcessFile) => {
    setDisplaySaveFileMessage(true);
    if (file.file_contents_hash) {
      setProcessModelFile(file);
    }
    if (!params.file_name) {
      const fileNameWithExtension = `${newFileName}.${searchParams.get(
        'file_type',
      )}`;
      navigate(
        `/process-models/${modifiedProcessModelId}/files/${fileNameWithExtension}`,
      );
    } else {
      getProcessModelSpecs();
    }
  };

  const saveDiagram = (bpmnXML: any, fileName = params.file_name) => {
    setDisplaySaveFileMessage(false);
    removeError();
    setBpmnXmlForDiagramRendering(bpmnXML);

    let url = `/process-models/${modifiedProcessModelId}/files`;
    let httpMethod = 'PUT';
    let fileNameWithExtension = fileName;

    if (newFileName) {
      fileNameWithExtension = `${newFileName}.${searchParams.get('file_type')}`;
      httpMethod = 'POST';
    } else {
      url += `/${fileNameWithExtension}`;
      if (processModelFile && processModelFile.file_contents_hash) {
        url += `?file_contents_hash=${processModelFile.file_contents_hash}`;
      }
    }
    if (!fileNameWithExtension) {
      handleShowFileNameEditor();
      return;
    }

    const bpmnFile = new File([bpmnXML], fileNameWithExtension);
    const formData = new FormData();
    formData.append('file', bpmnFile);
    formData.append('fileName', bpmnFile.name);

    HttpService.makeCallToBackend({
      path: url,
      successCallback: navigateToProcessModelFile,
      failureCallback: addError,
      httpMethod,
      postBody: formData,
    });

    // after saving the file, make sure we null out newFileName
    // so it does not get used over the params
    setNewFileName('');
    setDiagramHasChanges(false);
  };

  const onElementsChanged = useCallback(() => {
    setDiagramHasChanges(true);
  }, []);

  const onDeleteFile = (fileName = params.file_name) => {
    const url = `/process-models/${modifiedProcessModelId}/files/${fileName}`;
    const httpMethod = 'DELETE';

    const navigateToProcessModelShow = (_httpResult: any) => {
      navigate(`/process-models/${modifiedProcessModelId}`);
    };
    HttpService.makeCallToBackend({
      path: url,
      successCallback: navigateToProcessModelShow,
      httpMethod,
    });
  };

  const onSetPrimaryFile = (fileName = params.file_name) => {
    const url = `/process-models/${modifiedProcessModelId}`;
    const httpMethod = 'PUT';

    const navigateToProcessModelShow = (_httpResult: any) => {
      navigate(url);
    };
    const processModelToPass = {
      primary_file_name: fileName,
    };
    HttpService.makeCallToBackend({
      path: url,
      successCallback: navigateToProcessModelShow,
      httpMethod,
      postBody: processModelToPass,
    });
  };

  const handleFileNameSave = (event: any) => {
    event.preventDefault();
    if (!newFileName) {
      setProcessModelFileInvalidText(
        t('diagram_file_name_editor_error_required'),
      );
      return;
    }
    setProcessModelFileInvalidText('');
    setShowFileNameEditor(false);
    saveDiagram(bpmnXmlForDiagramRendering);
  };

  const newFileNameBox = () => {
    const fileExtension = `.${searchParams.get('file_type')}`;
    return (
      <Dialog
        open={showFileNameEditor}
        onClose={handleFileNameCancel}
        aria-labelledby="modal-modal-title"
        aria-describedby="modal-modal-description"
      >
        <Box sx={{ p: 4 }}>
          <h2 id="modal-modal-title">{t('diagram_file_name_editor_title')}</h2>
          <Grid container spacing={2}>
            <Grid size={{ xs: 8 }}>
              <TextField
                id="process_model_file_name"
                label={t('diagram_file_name_editor_label')}
                value={newFileName}
                onChange={(e: any) => setNewFileName(e.target.value)}
                error={!!processModelFileInvalidText}
                helperText={processModelFileInvalidText}
                size="small"
                autoFocus
                fullWidth
              />
            </Grid>
            <Grid size={{ xs: 4 }}>{fileExtension}</Grid>
          </Grid>
          <ButtonGroup>
            <Button onClick={handleFileNameSave}>{t('save_changes')}</Button>
            <Button onClick={handleFileNameCancel}>{t('cancel')}</Button>
          </ButtonGroup>
        </Box>
      </Dialog>
    );
  };

  const resetUnitTextResult = () => {
    setScriptUnitTestResult(null);
    const styleSheet = document.styleSheets[0];
    const ruleList = styleSheet.cssRules;
    for (let ii = ruleList.length - 1; ii >= 0; ii -= 1) {
      const regexp = new RegExp(
        `^.${failingScriptLineClassNamePrefix}_.*::after `,
      );
      if (ruleList[ii].cssText.match(regexp)) {
        styleSheet.deleteRule(ii);
      }
    }
  };

  // Note: API-based callbacks are now provided by useBpmnEditorCallbacks hook

  const getScriptUnitTestElements = (element: any) => {
    const { extensionElements } = element.businessObject;
    if (extensionElements && extensionElements.values.length > 0) {
      const unitTestModdleElements = extensionElements
        .get('values')
        .filter(function getInstanceOfType(e: any) {
          return e.$instanceOf('spiffworkflow:UnitTests');
        })[0];
      if (unitTestModdleElements) {
        return unitTestModdleElements.unitTests;
      }
    }
    return [];
  };

  const setScriptUnitTestElementWithIndex = useCallback(
    (scriptIndex: number, element: any) => {
      const unitTestsModdleElements = getScriptUnitTestElements(element);
      if (unitTestsModdleElements.length > 0) {
        setCurrentScriptUnitTest(unitTestsModdleElements[scriptIndex]);
        setCurrentScriptUnitTestIndex(scriptIndex);
      }
    },
    [],
  );

  useEffect(() => {
    if (!scriptEditorState) {
      return;
    }
    setScriptUnitTestElementWithIndex(0, scriptEditorState.element);
  }, [scriptEditorState, setScriptUnitTestElementWithIndex]);

  const handleScriptEditorClose = () => {
    fireScriptUpdate(scriptEventBus, scriptType, scriptText, scriptElement);
    resetUnitTextResult();
    closeScriptEditor();
  };

  const handleEditorScriptTestUnitInputChange = (value: any) => {
    if (currentScriptUnitTest) {
      currentScriptUnitTest.inputJson.value = value;
      (scriptModeling as any).updateProperties(scriptElement, {});
    }
  };

  const handleEditorScriptTestUnitOutputChange = (value: any) => {
    if (currentScriptUnitTest) {
      currentScriptUnitTest.expectedOutputJson.value = value;
      (scriptModeling as any).updateProperties(scriptElement, {});
    }
  };

  const generalEditorOptions = () => {
    return {
      glyphMargin: false,
      folding: false,
      lineNumbersMinChars: 0,
    };
  };

  const jsonEditorOptions = () => {
    return Object.assign(generalEditorOptions(), {
      minimap: { enabled: false },
      folding: true,
    });
  };

  const setPreviousScriptUnitTest = () => {
    resetUnitTextResult();
    const newScriptIndex = currentScriptUnitTestIndex - 1;
    if (newScriptIndex >= 0) {
      setScriptUnitTestElementWithIndex(newScriptIndex, scriptElement);
    }
  };

  const setNextScriptUnitTest = () => {
    resetUnitTextResult();
    const newScriptIndex = currentScriptUnitTestIndex + 1;
    const unitTestsModdleElements = getScriptUnitTestElements(scriptElement);
    if (newScriptIndex < unitTestsModdleElements.length) {
      setScriptUnitTestElementWithIndex(newScriptIndex, scriptElement);
    }
  };

  const processScriptUnitTestRunResult = (result: any) => {
    if ('result' in result) {
      setScriptUnitTestResult(result);
      if (
        result.line_number &&
        result.error &&
        editorRef.current &&
        monacoRef.current
      ) {
        const currentClassName = `${failingScriptLineClassNamePrefix}_${makeid(
          7,
        )}`;

        // document.documentElement.style.setProperty causes the content property to go away
        // so add the rule dynamically instead of changing a property variable
        document.styleSheets[0].addRule(
          `.${currentClassName}::after`,
          `content: "  # ${result.error.replaceAll('"', '')}"; color: red`,
        );

        const lineLength =
          scriptText.split('\n')[result.line_number - 1].length + 1;

        const editorRefToUse = editorRef.current as any;
        editorRefToUse.deltaDecorations(
          [],
          [
            {
              // Range(lineStart, column, lineEnd, column)
              range: new (monacoRef.current as any).Range(
                result.line_number,
                lineLength,
              ),
              options: { afterContentClassName: currentClassName },
            },
          ],
        );
      }
    }
  };

  const runCurrentUnitTest = () => {
    if (currentScriptUnitTest && scriptElement) {
      let inputJson = '';
      let expectedJson = '';
      try {
        inputJson = JSON.parse(currentScriptUnitTest.inputJson.value);
        expectedJson = JSON.parse(
          currentScriptUnitTest.expectedOutputJson.value,
        );
      } catch (_) {
        setScriptUnitTestResult({
          result: false,
          error: t('diagram_errors_json_formatting'),
        });
        return;
      }

      resetUnitTextResult();
      HttpService.makeCallToBackend({
        path: `/process-models/${modifiedProcessModelId}/script-unit-tests/run`,
        httpMethod: 'POST',
        successCallback: processScriptUnitTestRunResult,
        postBody: {
          bpmn_task_identifier: (scriptElement as any).id,
          python_script: scriptText,
          input_json: inputJson,
          expected_output_json: expectedJson,
        },
      });
    }
  };

  const unitTestFailureElement = () => {
    if (scriptUnitTestResult && scriptUnitTestResult.result === false) {
      let errorObject = '';
      if (scriptUnitTestResult.context) {
        errorObject = t('diagram_errors_unexpected_result');
      } else if (scriptUnitTestResult.line_number) {
        errorObject = t('diagram_errors_script_error_line', {
          lineNumber: scriptUnitTestResult.line_number,
        });
      } else {
        errorObject = t('diagram_errors_script_error_generic', {
          errorMessage: JSON.stringify(scriptUnitTestResult.error),
        });
      }
      let errorStringElement = <span>{errorObject}</span>;

      let errorContextElement = null;

      if (scriptUnitTestResult.context) {
        errorStringElement = (
          <span>
            Unexpected result. Please see the expected / actual comparison
            below.
          </span>
        );
        let outputJson = '{}';
        if (currentScriptUnitTest) {
          outputJson = JSON.stringify(
            JSON.parse(currentScriptUnitTest.expectedOutputJson.value),
            null,
            '  ',
          );
        }
        const contextJson = JSON.stringify(
          scriptUnitTestResult.context,
          null,
          '  ',
        );
        errorContextElement = (
          <DiffEditor
            height={200}
            width="auto"
            originalLanguage="json"
            modifiedLanguage="json"
            options={Object.assign(jsonEditorOptions(), {})}
            original={outputJson}
            modified={contextJson}
          />
        );
      }
      return (
        <span style={{ color: 'red', fontSize: '1em' }}>
          {errorStringElement}
          {errorContextElement}
        </span>
      );
    }
    return null;
  };

  const scriptUnitTestEditorElement = () => {
    if (currentScriptUnitTest) {
      let previousButtonDisable = true;
      if (currentScriptUnitTestIndex > 0) {
        previousButtonDisable = false;
      }
      let nextButtonDisable = true;
      const unitTestsModdleElements = getScriptUnitTestElements(scriptElement);
      if (currentScriptUnitTestIndex < unitTestsModdleElements.length - 1) {
        nextButtonDisable = false;
      }

      // unset current unit test if all tests were deleted
      if (unitTestsModdleElements.length < 1) {
        setCurrentScriptUnitTest(null);
        setCurrentScriptUnitTestIndex(-1);
      }

      let scriptUnitTestResultBoolElement = null;
      if (scriptUnitTestResult) {
        scriptUnitTestResultBoolElement = (
          <>
            {scriptUnitTestResult.result === true && (
              <IconButton color="success">
                <Check />
              </IconButton>
            )}
            {scriptUnitTestResult.result === false && (
              <IconButton color="error">
                <Close />
              </IconButton>
            )}
          </>
        );
      }
      let inputJson = currentScriptUnitTest.inputJson.value;
      let outputJson = currentScriptUnitTest.expectedOutputJson.value;
      try {
        inputJson = JSON.stringify(
          JSON.parse(currentScriptUnitTest.inputJson.value),
          null,
          '  ',
        );
        outputJson = JSON.stringify(
          JSON.parse(currentScriptUnitTest.expectedOutputJson.value),
          null,
          '  ',
        );
      } catch (_) {
        // Attemping to format the json failed -- it's invalid.
      }

      return (
        <main>
          <Grid container spacing={2}>
            <Grid size={{ xs: 6 }}>
              <p className="with-top-margin-for-unit-test-name">
                {t('diagram_script_editor_unit_test_title', {
                  testId: currentScriptUnitTest.id,
                })}
              </p>
            </Grid>
            <Grid size={{ xs: 6 }}>
              <ButtonGroup>
                <IconButton
                  onClick={setPreviousScriptUnitTest}
                  disabled={previousButtonDisable}
                >
                  <SkipPrevious />
                </IconButton>
                <IconButton
                  onClick={setNextScriptUnitTest}
                  disabled={nextButtonDisable}
                >
                  <SkipNext />
                </IconButton>
                <IconButton onClick={runCurrentUnitTest}>
                  <PlayArrow />
                </IconButton>
                {scriptUnitTestResultBoolElement}
              </ButtonGroup>
            </Grid>
          </Grid>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12 }}>{unitTestFailureElement()}</Grid>
          </Grid>
          <Grid container spacing={2}>
            <Grid size={{ xs: 6 }}>
              <div>{t('diagram_script_editor_unit_test_input_json')}</div>
              <div>
                <Editor
                  height={500}
                  width="auto"
                  defaultLanguage="json"
                  options={Object.assign(jsonEditorOptions(), {})}
                  defaultValue={inputJson}
                  onChange={handleEditorScriptTestUnitInputChange}
                />
              </div>
            </Grid>
            <Grid size={{ xs: 6 }}>
              <div>
                {t('diagram_script_editor_unit_test_expected_output_json')}
              </div>
              <div>
                <Editor
                  height={500}
                  width="auto"
                  defaultLanguage="json"
                  options={Object.assign(jsonEditorOptions(), {})}
                  defaultValue={outputJson}
                  onChange={handleEditorScriptTestUnitOutputChange}
                />
              </div>
            </Grid>
          </Grid>
        </main>
      );
    }
    return null;
  };

  /* Main python script editor user works in */
  const editorWindow = () => {
    return (
      <Editor
        height={500}
        width="auto"
        options={generalEditorOptions()}
        defaultLanguage="python"
        defaultValue={scriptText}
        value={scriptText}
        onChange={handleEditorScriptChange}
        onMount={handleEditorDidMount}
      />
    );
  };

  /**
   * When user clicks script assist button, set useScriptAssistQuery hook with query.
   * This will async update scriptAssistResult as needed.
   */
  const handleProcessScriptAssist = () => {
    if (scriptAssistValue) {
      try {
        setScriptAssistQuery(scriptAssistValue);
        setScriptAssistError(null);
      } catch (error) {
        setScriptAssistError(
          t('diagram_script_assist_error_processing', { error }),
        );
      }
    } else {
      setScriptAssistError(
        t('diagram_script_assist_error_instructions_required'),
      );
    }
  };

  /* If the Script Assist tab is enabled (via scriptAssistEnabled), this is the UI */
  const scriptAssistWindow = () => {
    return (
      <>
        <TextareaAutosize
          placeholder={t('diagram_script_assist_placeholder')}
          minRows={20}
          value={scriptAssistValue}
          onChange={(e: any) => setScriptAssistValue(e.target.value)}
          style={{ width: '100%' }}
        />
        <Stack
          direction="row"
          justifyContent="flex-end"
          alignItems="center"
          spacing={2}
        >
          {scriptAssistError && (
            <div style={{ color: 'red' }}>{scriptAssistError}</div>
          )}
          {scriptAssistLoading && <CircularProgress />}
          <Button
            variant="contained"
            onClick={() => handleProcessScriptAssist()}
            disabled={scriptAssistLoading}
          >
            {t('diagram_script_assist_button')}
          </Button>
        </Stack>
      </>
    );
  };

  const scriptEditor = () => {
    return (
      <Grid container>
        <Grid size={{ xs: 12 }}>{editorWindow()}</Grid>
      </Grid>
    );
  };

  const scriptEditorWithAssist = () => {
    return (
      <Grid container>
        <Grid size={{ xs: 7 }}>{editorWindow()}</Grid>
        <Grid size={{ xs: 5 }}>
          <Tooltip title={t('diagram_script_assist_tooltip')}>
            <Stack direction="row" alignItems="center" spacing={1}>
              <Info fontSize="small" />
              <span>{t('diagram_script_assist_hint')}</span>
            </Stack>
          </Tooltip>
          {scriptAssistWindow()}
        </Grid>
      </Grid>
    );
  };

  const scriptEditorAndTests = () => {
    const handleTabChange = (_event: SyntheticEvent, newValue: number) => {
      setScriptEditorTabValue(newValue);
    };

    if (!scriptEditorState) {
      return null;
    }
    let scriptName = '';
    if (scriptElement) {
      scriptName = (scriptElement as any).di.bpmnElement.name;
    }
    return (
      <Dialog
        className="wide-dialog"
        open={!!scriptEditorState}
        onClose={handleScriptEditorClose}
        aria-labelledby="modal-modal-title"
        aria-describedby="modal-modal-description"
      >
        <Box sx={{ p: 4 }}>
          <h2 id="modal-modal-title">
            {t('diagram_script_editor_title', { scriptName })}
          </h2>
          <Tabs value={scriptEditorTabValue} onChange={handleTabChange}>
            <Tab label={t('diagram_script_editor_tab_script_editor')} />
            {scriptAssistEnabled && (
              <Tab label={t('diagram_script_editor_tab_script_assist')} />
            )}
            <Tab label={t('diagram_script_editor_tab_unit_tests')} />
          </Tabs>
          <Box>
            <TabPanel value={scriptEditorTabValue} index={0}>
              {scriptEditor()}
            </TabPanel>
            <TabPanel value={scriptEditorTabValue} index={1}>
              {scriptUnitTestEditorElement()}
            </TabPanel>
            {scriptAssistEnabled && (
              <TabPanel value={scriptEditorTabValue} index={2}>
                {scriptEditorWithAssist()}
              </TabPanel>
            )}
          </Box>
          <Button onClick={handleScriptEditorClose}>{t('close')}</Button>
        </Box>
      </Dialog>
    );
  };

  const handleMarkdownEditorClose = () => {
    closeMarkdownEditorWithUpdate(
      markdownEventBus,
      markdownText || '',
      closeMarkdownEditor,
    );
  };

  const markdownEditorTextArea = (props: any) => {
    return <TextareaAutosize {...props} />;
  };

  const markdownEditor = () => {
    if (!markdownEditorState) {
      return null;
    }
    return (
      <Dialog
        className="wide-dialog"
        open={!!markdownEditorState}
        onClose={handleMarkdownEditorClose}
        aria-labelledby="modal-modal-title"
        aria-describedby="modal-modal-description"
      >
        <Box sx={{ p: 4 }}>
          <h2 id="modal-modal-title">{t('diagram_markdown_editor_title')}</h2>
          <div data-color-mode="light">
            <MDEditor
              height={500}
              highlightEnable={false}
              value={markdownText}
              onChange={setMarkdownText}
              components={{
                textarea: markdownEditorTextArea,
              }}
            />
          </div>
          <Button onClick={handleMarkdownEditorClose}>{t('close')}</Button>
        </Box>
      </Dialog>
    );
  };

  const handleMessageEditorClose = () => {
    closeMessageEditorAndRefresh(
      messageEditorState?.event,
      closeMessageEditor,
      onMessagesRequested,
    );
  };

  const handleMessageEditorSave = (_event: any) => {
    if (messageEditorState?.event?.eventBus) {
      fireMessageSave(messageEditorState.event.eventBus);
    }
  };

  const messageEditor = () => {
    // do not render this component until we actually want to display it
    if (!messageEditorState) {
      return null;
    }
    return (
      <Dialog
        className="wide-dialog"
        open={!!messageEditorState}
        onClose={handleMessageEditorClose}
        aria-labelledby="modal-modal-title"
        aria-describedby="modal-modal-description"
      >
        <Box sx={{ p: 4 }}>
          <h2 id="modal-modal-title">{t('diagram_message_editor_title')}</h2>
          <p>{t('diagram_message_editor_description')}</p>
          <div data-color-mode="light">
            <MessageEditor
              modifiedProcessGroupIdentifier={getGroupFromModifiedModelId(
                modifiedProcessModelId,
              )}
              messageId={messageEditorState.messageId}
              correlationProperties={messageEditorState.correlationProperties}
              messageEvent={messageEditorState.event}
              elementId={messageEditorState.elementId}
            />
          </div>
          <Button onClick={handleMessageEditorSave}>
            {t('diagram_message_editor_save')}
          </Button>
          <Button onClick={handleMessageEditorClose}>
            {t('diagram_message_editor_close')}
          </Button>
        </Box>
      </Dialog>
    );
  };

  const processSearchOnClose = (selection: ProcessReference) => {
    selectProcessSearchResult(selection?.identifier);
  };

  const processModelSelector = () => {
    if (!processSearchState) {
      return null;
    }
    return (
      <Dialog
        className="wide-dialog"
        open={!!processSearchState}
        onClose={processSearchOnClose}
        aria-labelledby="modal-modal-title"
        aria-describedby="modal-modal-description"
      >
        <Box sx={{ p: 4 }}>
          <h2 id="modal-modal-title">
            {t('diagram_process_model_selector_title')}
          </h2>
          <ProcessSearch
            height="500px"
            onChange={processSearchOnClose}
            processes={processes}
            titleText={t('diagram_process_model_selector_search_placeholder')}
            placeholderText={t('choose_a_process')}
          />
        </Box>
      </Dialog>
    );
  };

  // Note: findFileNameForReferenceId is now provided by the bpmn-js-spiffworkflow-react package

  const onLaunchBpmnEditor = useCallback(
    (processId: string) => {
      const openProcessModelFileInNewTab = (
        processReference: ProcessReference,
      ) => {
        const path = generatePath(
          '/process-models/:process_model_path/files/:file_name',
          {
            process_model_path: modifyProcessIdentifierForPathParam(
              processReference.relative_location,
            ),
            file_name: processReference.file_name,
          },
        );
        window.open(path);
      };

      const openFileNameForProcessId = (
        processesReferences: ProcessReference[],
      ) => {
        const processRef = processesReferences.find((p) => {
          return p.identifier === processId;
        });
        if (processRef) {
          openProcessModelFileInNewTab(processRef);
        }
      };

      const processRef = processes.find((p) => p.identifier === processId);
      if (processRef) {
        openProcessModelFileInNewTab(processRef);
        return;
      }

      refreshProcesses().then((freshProcesses) => {
        openFileNameForProcessId(freshProcesses);
      });
    },
    [processes, refreshProcesses],
  );

  const onLaunchJsonSchemaEditor = useCallback(
    (element: any, fileName: string, eventBus: any) => {
      const url = import.meta.env.VITE_SPIFFWORKFLOW_FRONTEND_LAUNCH_EDITOR_URL;
      if (url) {
        window.open(
          `${url}?processModelId=${params.process_model_id || ''}&fileName=${fileName || ''}`,
          '_blank',
        );
        return;
      }
      launchJsonSchemaEditor(element, fileName, eventBus);
    },
    [params.process_model_id, launchJsonSchemaEditor],
  );

  const addNewFileIfNotExist = () => {
    if (!processModel) {
      return;
    }
    const { files } = processModel;
    const fileNames = [
      jsonSchemaFileName,
      jsonSchemaFileName.replace('-schema.json', '-uischema.json'),
      jsonSchemaFileName.replace('-schema.json', '-exampledata.json'),
    ];

    const newFiles = fileNames
      .filter((name) => !files.some((f) => f.name === name))
      .map((name) => ({
        content_type: 'application/json',
        last_modified: '',
        name,
        process_model_id: processModel?.id || '',
        references: [],
        size: 0,
        type: 'json',
      }));

    if (newFiles.length > 0) {
      // we have to push items onto the existing files array.
      // Otherwise react thinks more of the state changed than we want.
      newFiles.forEach((file: any) => {
        files.push(file);
      });
      setProcessModel((prevProcessModel: any) => ({
        ...prevProcessModel,
        files,
      }));
    }
  };

  const handleJsonSchemaEditorClose = () => {
    closeJsonSchemaEditorWithUpdate(
      fileEventBus,
      jsonSchemaFileName,
      closeJsonSchemaEditor,
      addNewFileIfNotExist,
    );
  };

  const jsonSchemaEditor = () => {
    if (!jsonSchemaEditorState || !permissionsLoaded) {
      return null;
    }
    return (
      <Dialog
        className="wide-dialog"
        open={!!jsonSchemaEditorState}
        onClose={handleJsonSchemaEditorClose}
        aria-labelledby="modal-modal-title"
        aria-describedby="modal-modal-description"
      >
        <Box sx={{ p: 4 }}>
          <h2 id="modal-modal-title">
            {t('diagram_json_schema_editor_title')}
          </h2>
          <ReactFormBuilder
            processModelId={params.process_model_id || ''}
            fileName={jsonSchemaFileName}
            onFileNameSet={setJsonSchemaFileName}
            canUpdateFiles={ability.can(
              'POST',
              targetUris.processModelFileCreatePath,
            )}
            canCreateFiles={ability.can(
              'PUT',
              targetUris.processModelFileCreatePath,
            )}
            pythonWorker={pythonWorker}
          />
          <Button onClick={handleJsonSchemaEditorClose}>{t('close')}</Button>
        </Box>
      </Dialog>
    );
  };

  const onLaunchDmnEditor = useCallback(
    (processId: string) => {
      const file = findFileNameForReferenceId(processModel, processId, 'dmn');
      let path = '';
      if (file) {
        path = generatePath(
          '/process-models/:process_model_id/files/:file_name',
          {
            process_model_id: params.process_model_id || null,
            file_name: file.name,
          },
        );
        window.open(path);
      } else {
        path = generatePath(
          '/process-models/:process_model_id/files?file_type=dmn',
          {
            process_model_id: params.process_model_id || null,
          },
        );
      }
      window.open(path);
    },
    [processModel, params.process_model_id],
  );

  const isDmn = () => {
    const fileName = params.file_name || '';
    return searchParams.get('file_type') === 'dmn' || fileName.endsWith('.dmn');
  };

  const appropriateEditor = () => {
    if (isDmn()) {
      return (
        <ReactDiagramEditor
          diagramType="dmn"
          diagramXML={bpmnXmlForDiagramRendering}
          fileName={params.file_name}
          onDeleteFile={onDeleteFile}
          processModelId={params.process_model_id || ''}
          saveDiagram={saveDiagram}
        />
      );
    }
    // let this be undefined (so we won't display the button) unless the
    // current primary_file_name is different from the one we're looking at.
    let onSetPrimaryFileCallback;
    if (
      processModel &&
      params.file_name &&
      params.file_name !== processModel.primary_file_name
    ) {
      onSetPrimaryFileCallback = onSetPrimaryFile;
    }
    return (
      <ReactDiagramEditor
        activeUserElement={<ActiveUsers />}
        callers={callers}
        diagramType="bpmn"
        diagramXML={bpmnXmlForDiagramRendering}
        disableSaveButton={!diagramHasChanges}
        fileName={params.file_name}
        isPrimaryFile={params.file_name === processModel?.primary_file_name}
        processModel={processModel}
        onDataStoresRequested={bpmnEditorCallbacks.onDataStoresRequested}
        onDeleteFile={onDeleteFile}
        onDmnFilesRequested={bpmnEditorCallbacks.onDmnFilesRequested}
        onElementsChanged={onElementsChanged}
        onJsonSchemaFilesRequested={bpmnEditorCallbacks.onJsonSchemaFilesRequested}
        onLaunchBpmnEditor={onLaunchBpmnEditor}
        onLaunchDmnEditor={onLaunchDmnEditor}
        onLaunchJsonSchemaEditor={onLaunchJsonSchemaEditor}
        onLaunchMarkdownEditor={onLaunchMarkdownEditor}
        onLaunchMessageEditor={onLaunchMessageEditor}
        onLaunchScriptEditor={onLaunchScriptEditor}
        onMessagesRequested={bpmnEditorCallbacks.onMessagesRequested}
        onSearchProcessModels={onSearchProcessModels}
        onServiceTasksRequested={bpmnEditorCallbacks.onServiceTasksRequested}
        onSetPrimaryFile={onSetPrimaryFileCallback}
        processModelId={params.process_model_id || ''}
        saveDiagram={saveDiagram}
      />
    );
  };

  const saveFileMessage = () => {
    if (displaySaveFileMessage) {
      return (
        <Notification
          title={t('file_saved_title')}
          onClose={() => setDisplaySaveFileMessage(false)}
          hideCloseButton
          timeout={3000}
        >
          {t('file_saved_message')}
        </Notification>
      );
    }
    return null;
  };

  const unsavedChangesMessage = () => {
    if (diagramHasChanges) {
      return (
        <Can I="PUT" a={targetUris.processModelFileShowPath} ability={ability}>
          <Notification
            title={t('diagram_notifications_unsaved_changes_title')}
            type="error"
            data-testid="process-model-file-changed"
            hideCloseButton
          >
            {t('diagram_notifications_unsaved_changes_message')}
          </Notification>
        </Can>
      );
    }
    return null;
  };

  const pageModals = () => {
    return (
      <>
        {newFileNameBox()}
        {scriptEditorAndTests()}
        {markdownEditor()}
        {jsonSchemaEditor()}
        {processModelSelector()}
        {messageEditor()}
      </>
    );
  };

  // if a file name is not given then this is a new model and the ReactDiagramEditor component will handle it
  if ((bpmnXmlForDiagramRendering || !params.file_name) && processModel) {
    const processModelFileName = processModelFile ? processModelFile.name : '';
    return (
      <>
        <ProcessBreadcrumb
          hotCrumbs={[
            [t('process_groups'), '/process-groups'],
            {
              entityToExplode: processModel,
              entityType: 'process-model',
              linkLastItem: true,
            },
            [processModelFileName],
          ]}
        />
        <h1>
          {t('process_model_file', { fileName: processModelFileName || '---' })}
        </h1>

        {pageModals()}

        {unsavedChangesMessage()}
        {saveFileMessage()}
        {appropriateEditor()}
        <div id="diagram-container" />
      </>
    );
  }
  return null;
}
