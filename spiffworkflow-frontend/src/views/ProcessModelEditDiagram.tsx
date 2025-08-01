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
  Grid,
  Box,
  Stack,
  TextareaAutosize,
  CircularProgress,
  IconButton,
  Tooltip,
} from '@mui/material';
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
  getGroupFromModifiedModelId,
  makeid,
  modifyProcessIdentifierForPathParam,
  setPageTitle,
} from '../helpers';
import {
  CorrelationProperties,
  PermissionsToCheck,
  ProcessFile,
  ProcessModel,
  ProcessReference,
} from '../interfaces';
import ProcessSearch from '../components/ProcessSearch';
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

  const [scriptText, setScriptText] = useState<string>('');
  const [scriptType, setScriptType] = useState<string>('');
  const [fileEventBus, setFileEventBus] = useState<any>(null);
  const [jsonSchemaFileName, setJsonSchemaFileName] = useState<string>('');
  const [showJsonSchemaEditor, setShowJsonSchemaEditor] = useState(false);

  const [scriptEventBus, setScriptEventBus] = useState<any>(null);
  const [scriptModeling, setScriptModeling] = useState(null);
  const [scriptElement, setScriptElement] = useState(null);
  const [showScriptEditor, setShowScriptEditor] = useState(false);
  const handleShowScriptEditor = () => setShowScriptEditor(true);

  const [markdownText, setMarkdownText] = useState<string | undefined>('');
  const [markdownEventBus, setMarkdownEventBus] = useState<any>(null);
  const [showMarkdownEditor, setShowMarkdownEditor] = useState(false);
  const [showMessageEditor, setShowMessageEditor] = useState(false);
  const [messageId, setMessageId] = useState<string>('');
  const [elementId, setElementId] = useState<string>('');
  const [correlationProperties, setCorrelationProperties] =
    useState<CorrelationProperties | null>(null);
  const [showProcessSearch, setShowProcessSearch] = useState(false);
  const [processSearchEventBus, setProcessSearchEventBus] = useState<any>(null);
  const [processSearchElement, setProcessSearchElement] = useState<any>(null);
  const [processes, setProcesses] = useState<ProcessReference[]>([]);
  const [displaySaveFileMessage, setDisplaySaveFileMessage] =
    useState<boolean>(false);
  const [processModelFileInvalidText, setProcessModelFileInvalidText] =
    useState<string>('');
  const [scriptEditorTabValue, setScriptEditorTabValue] = useState<number>(0);

  const [messageEvent, setMessageEvent] = useState<any>(null);

  const handleShowMarkdownEditor = () => setShowMarkdownEditor(true);

  const handleShowMessageEditor = () => setShowMessageEditor(true);

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

  const getProcessesCallback = useCallback((onProcessesFetched?: Function) => {
    const processResults = (result: any) => {
      const selectionArray = result.map((item: any) => {
        const label = `${item.display_name} (${item.identifier})`;
        Object.assign(item, { label });
        return item;
      });
      setProcesses(selectionArray);
      if (onProcessesFetched) {
        onProcessesFetched(selectionArray);
      }
    };
    HttpService.makeCallToBackend({
      path: `/processes`,
      successCallback: processResults,
    });

    const worker = new Worker(
      new URL('/src/workers/python.ts', import.meta.url),
    );

    setPythonWorker(worker);
  }, []);

  const handleEditorScriptChange = (value: any) => {
    setScriptText(value);
  };

  useEffect(() => {
    getProcessesCallback();
  }, [getProcessesCallback]);

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
    const path = `/process-models/${modifiedProcessModelId}/specs`;

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
            <Grid item xs={8}>
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
            <Grid item xs={4}>
              {fileExtension}
            </Grid>
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

  const makeApiHandler = (event: any) => {
    return function fireEvent(results: any) {
      event.eventBus.fire('spiff.service_tasks.returned', {
        serviceTaskOperators: results,
      });
    };
  };

  const makeDataStoresApiHandler = (event: any) => {
    return function fireEvent(results: any) {
      event.eventBus.fire('spiff.data_stores.returned', {
        options: results,
      });
    };
  };

  const onServiceTasksRequested = useCallback((event: any) => {
    HttpService.makeCallToBackend({
      path: `/service-tasks`,
      successCallback: makeApiHandler(event),
    });
  }, []);

  const onDataStoresRequested = useCallback(
    (event: any) => {
      const processGroupIdentifier =
        processModel?.parent_groups?.slice(-1).pop()?.id ?? '';
      HttpService.makeCallToBackend({
        path: `/data-stores?upsearch=true&process_group_identifier=${processGroupIdentifier}`,
        successCallback: makeDataStoresApiHandler(event),
      });
    },
    [processModel?.parent_groups],
  );

  const onJsonSchemaFilesRequested = useCallback(
    (event: any) => {
      const re = /.*[-.]schema.json/;
      if (processModel?.files) {
        const jsonFiles = processModel.files.filter((f) => f.name.match(re));
        const options = jsonFiles.map((f) => {
          return { label: f.name, value: f.name };
        });
        event.eventBus.fire('spiff.json_schema_files.returned', { options });
      } else {
        console.error('There is no process Model.');
      }
    },
    [processModel?.files],
  );

  const onDmnFilesRequested = useCallback(
    (event: any) => {
      if (processModel?.files) {
        const dmnFiles = processModel.files.filter((f) => f.type === 'dmn');
        const options: any[] = [];
        dmnFiles.forEach((file) => {
          file.references.forEach((ref) => {
            options.push({ label: ref.display_name, value: ref.identifier });
          });
        });
        event.eventBus.fire('spiff.dmn_files.returned', { options });
      } else {
        console.error('There is no process model.');
      }
    },
    [processModel?.files],
  );

  const makeMessagesRequestedHandler = (event: any) => {
    return function fireEvent(results: any) {
      event.eventBus.fire('spiff.messages.returned', {
        configuration: results,
      });
    };
  };
  const onMessagesRequested = useCallback(
    (event: any) => {
      // it is perfectly reasonable to access the edit diagram page in read only mode when you actually don't have access to edit.
      // this is awkward in terms of functionality like this, where we are fetching the relevant list of messages to show in the
      // properties panel. since message_model_list is a different permission, you may not have access to it even though you have
      // access to the read the process model. we also considered automatically giving you access to read message_model_list
      // when you have read access to the process model, but this seemed easier and more in line with the current backend permission system,
      // where we normally only pork barrel permissions on top of "start" and "all."
      if (ability.can('GET', targetUris.messageModelListPath)) {
        HttpService.makeCallToBackend({
          path: targetUris.messageModelListPath,
          successCallback: makeMessagesRequestedHandler(event),
        });
      }
    },
    [ability, targetUris.messageModelListPath],
  );

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

  const onLaunchScriptEditor = useCallback(
    (
      element: any,
      script: string,
      scriptTypeString: string,
      eventBus: any,
      modeling: any,
    ) => {
      // TODO: modeling is only needed for script unit tests.
      // we should update this to act like updating scripts
      // where we pass an event to bpmn-js
      setScriptModeling(modeling);
      setScriptText(script || '');
      setScriptType(scriptTypeString);
      setScriptEventBus(eventBus);
      setScriptElement(element);
      setScriptUnitTestElementWithIndex(0, element);
      handleShowScriptEditor();
    },
    [setScriptUnitTestElementWithIndex],
  );

  const handleScriptEditorClose = () => {
    scriptEventBus.fire('spiff.script.update', {
      scriptType,
      script: scriptText,
      element: scriptElement,
    });

    resetUnitTextResult();
    setShowScriptEditor(false);
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
            <Grid item xs={6}>
              <p className="with-top-margin-for-unit-test-name">
                {t('diagram_script_editor_unit_test_title', {
                  testId: currentScriptUnitTest.id,
                })}
              </p>
            </Grid>
            <Grid item xs={6}>
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
            <Grid item xs={12}>
              {unitTestFailureElement()}
            </Grid>
          </Grid>
          <Grid container spacing={2}>
            <Grid item xs={6}>
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
            <Grid item xs={6}>
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
        <Grid item xs={12}>
          {editorWindow()}
        </Grid>
      </Grid>
    );
  };

  const scriptEditorWithAssist = () => {
    return (
      <Grid container>
        <Grid item xs={7}>
          {editorWindow()}
        </Grid>
        <Grid item xs={5}>
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

    if (!showScriptEditor) {
      return null;
    }
    let scriptName = '';
    if (scriptElement) {
      scriptName = (scriptElement as any).di.bpmnElement.name;
    }
    return (
      <Dialog
        className="wide-dialog"
        open={showScriptEditor}
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
            {scriptAssistEnabled && (
              <TabPanel value={scriptEditorTabValue} index={1}>
                {scriptEditorWithAssist()}
              </TabPanel>
            )}
            <TabPanel value={scriptEditorTabValue} index={2}>
              {scriptUnitTestEditorElement()}
            </TabPanel>
          </Box>
          <Button onClick={handleScriptEditorClose}>{t('close')}</Button>
        </Box>
      </Dialog>
    );
  };

  const onLaunchMarkdownEditor = useCallback(
    (_element: any, markdown: string, eventBus: any) => {
      setMarkdownText(markdown || '');
      setMarkdownEventBus(eventBus);
      handleShowMarkdownEditor();
    },
    [],
  );

  const handleMarkdownEditorClose = () => {
    markdownEventBus.fire('spiff.markdown.update', {
      value: markdownText,
    });
    setShowMarkdownEditor(false);
  };

  const markdownEditorTextArea = (props: any) => {
    return <TextareaAutosize {...props} />;
  };

  const markdownEditor = () => {
    return (
      <Dialog
        className="wide-dialog"
        open={showMarkdownEditor}
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

  const onLaunchMessageEditor = useCallback((event: any) => {
    setMessageEvent(event);
    setMessageId(event.value.messageId);
    setElementId(event.value.elementId);
    setCorrelationProperties(event.value.correlation_properties);
    handleShowMessageEditor();
  }, []);

  const handleMessageEditorClose = () => {
    setShowMessageEditor(false);
    onMessagesRequested(messageEvent);
  };

  const handleMessageEditorSave = (_event: any) => {
    messageEvent.eventBus.fire('spiff.message.save');
  };

  const messageEditor = () => {
    // do not render this component until we actually want to display it
    if (!showMessageEditor) {
      return null;
    }
    return (
      <Dialog
        className="wide-dialog"
        open={showMessageEditor}
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
              messageId={messageId}
              correlationProperties={correlationProperties}
              messageEvent={messageEvent}
              elementId={elementId}
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

  const onSearchProcessModels = useCallback(
    (_processId: string, eventBus: any, element: any) => {
      setProcessSearchEventBus(eventBus);
      setProcessSearchElement(element);
      setShowProcessSearch(true);
    },
    [],
  );
  const processSearchOnClose = (selection: ProcessReference) => {
    if (selection) {
      processSearchEventBus.fire('spiff.callactivity.update', {
        element: processSearchElement,
        value: selection.identifier,
      });
    }
    setShowProcessSearch(false);
  };

  const processModelSelector = () => {
    return (
      <Dialog
        className="wide-dialog"
        open={showProcessSearch}
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
          />
        </Box>
      </Dialog>
    );
  };

  const findFileNameForReferenceId = useCallback(
    (id: string, type: string): ProcessFile | null => {
      // Given a reference id (like a process_id, or decision_id) finds the file
      // that contains that reference and returns it.
      let matchFile = null;
      if (processModel?.files) {
        const files = processModel.files.filter((f) => f.type === type);
        files.some((file) => {
          if (file.references.some((ref) => ref.identifier === id)) {
            matchFile = file;
            return true;
          }
          return false;
        });
      }
      return matchFile;
    },
    [processModel?.files],
  );

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

      // using the "setState" method with a function gives us access to the
      // most current state of processes. Otherwise it uses the stale state
      // when passing the callback to a non-React component like bpmn-js:
      //   https://stackoverflow.com/a/60643670/6090676
      setProcesses((upToDateProcesses: ProcessReference[]) => {
        const processRef = upToDateProcesses.find((p) => {
          return p.identifier === processId;
        });
        if (!processRef) {
          getProcessesCallback(openFileNameForProcessId);
        } else {
          openProcessModelFileInNewTab(processRef);
        }
        return upToDateProcesses;
      });
    },
    [getProcessesCallback],
  );

  const onLaunchJsonSchemaEditor = useCallback(
    (_element: any, fileName: string, eventBus: any) => {
      setFileEventBus(eventBus);
      setJsonSchemaFileName(fileName);
      setShowJsonSchemaEditor(true);
    },
    [],
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
    addNewFileIfNotExist();
    fileEventBus.fire('spiff.jsonSchema.update', {
      value: jsonSchemaFileName,
    });
    setShowJsonSchemaEditor(false);
  };

  const jsonSchemaEditor = () => {
    if (!showJsonSchemaEditor || !permissionsLoaded) {
      return null;
    }
    return (
      <Dialog
        className="wide-dialog"
        open={showJsonSchemaEditor}
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
      const file = findFileNameForReferenceId(processId, 'dmn');
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
    [findFileNameForReferenceId, params.process_model_id],
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
        onDataStoresRequested={onDataStoresRequested}
        onDeleteFile={onDeleteFile}
        onDmnFilesRequested={onDmnFilesRequested}
        onElementsChanged={onElementsChanged}
        onJsonSchemaFilesRequested={onJsonSchemaFilesRequested}
        onLaunchBpmnEditor={onLaunchBpmnEditor}
        onLaunchDmnEditor={onLaunchDmnEditor}
        onLaunchJsonSchemaEditor={onLaunchJsonSchemaEditor}
        onLaunchMarkdownEditor={onLaunchMarkdownEditor}
        onLaunchMessageEditor={onLaunchMessageEditor}
        onLaunchScriptEditor={onLaunchScriptEditor}
        onMessagesRequested={onMessagesRequested}
        onSearchProcessModels={onSearchProcessModels}
        onServiceTasksRequested={onServiceTasksRequested}
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
