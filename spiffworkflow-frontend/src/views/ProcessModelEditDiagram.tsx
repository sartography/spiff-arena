import {
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
  ButtonGroup,
  Stack,
  TextareaAutosize,
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
  useBpmnEditorTextEditorsState,
  useBpmnEditorScriptState,
  useScriptUnitTestsState,
  runScriptUnitTest,
  MessageEditorDialog,
  MarkdownEditorDialog,
  JsonSchemaEditorDialog,
  FileNameEditorDialog,
  ProcessSearchDialog,
  ScriptAssistPanel,
  ScriptEditorDialog,
  useDiagramNavigationStack,
  useDiagramNavigationHandlers,
  fireMessageSave,
  closeMarkdownEditorWithUpdate,
  closeJsonSchemaEditorWithUpdate,
  closeMessageEditorAndRefresh,
  closeScriptEditorWithUpdate,
} from '../../packages/bpmn-js-spiffworkflow-react/src';
import type { DiagramNavigationItem } from '../../packages/bpmn-js-spiffworkflow-react/src';
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

  // CRITICAL: params.process_model_id is ALREADY colon-separated from URL!
  const modifiedProcessModelId = params.process_model_id || '';

  const processModelPath = `process-models/${modifiedProcessModelId}`;

  const [callers, setCallers] = useState<ProcessReference[]>([]);

  const [pythonWorker, setPythonWorker] = useState<Worker | null>(null);

  const {
    stack: navigationStack,
    push: pushNavigation,
    reset: resetNavigation,
    popToIndex,
    updateTop,
  } = useDiagramNavigationStack();

  const prevNavigationKeyRef = useRef<string>('');

  const buildProcessFilePath = useCallback((item: DiagramNavigationItem) => {
    return generatePath('/process-models/:process_model_id/files/:file_name', {
      process_model_id: item.modifiedProcessModelId,
      file_name: item.fileName,
    });
  }, []);

  const handleEditorScriptChange = useCallback(
    (value: any) => {
      setScriptText(value);
    },
    [setScriptText],
  );

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

  useEffect(() => {
    if (!params.process_model_id || !params.file_name) {
      return;
    }
    const currentKey = `${params.process_model_id}:${params.file_name}`;
    if (prevNavigationKeyRef.current === currentKey) {
      return;
    }
    prevNavigationKeyRef.current = currentKey;

    const currentItem: DiagramNavigationItem = {
      modifiedProcessModelId: params.process_model_id,
      fileName: params.file_name,
    };
    const existingIndex = navigationStack.findIndex(
      (item) =>
        item.modifiedProcessModelId === currentItem.modifiedProcessModelId &&
        item.fileName === currentItem.fileName,
    );
    if (existingIndex === -1) {
      resetNavigation(currentItem);
      return;
    }
    if (existingIndex !== navigationStack.length - 1) {
      popToIndex(existingIndex);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.file_name, params.process_model_id, popToIndex, resetNavigation]);

  useEffect(() => {
    if (!processModelFile) {
      return;
    }
    updateTop({
      displayName: processModelFile.name,
    });
  }, [processModelFile, updateTop]);

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
  }, [scriptAssistResult, handleEditorScriptChange]);

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
      <FileNameEditorDialog
        open={showFileNameEditor}
        title={t('diagram_file_name_editor_title')}
        label={t('diagram_file_name_editor_label')}
        value={newFileName}
        fileExtension={fileExtension}
        errorText={processModelFileInvalidText}
        onChange={setNewFileName}
        onSave={handleFileNameSave}
        onCancel={handleFileNameCancel}
        saveLabel={t('save_changes')}
        cancelLabel={t('cancel')}
      />
    );
  };

  const resetUnitTextResult = () => {
    resetScriptUnitTestResult();
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

  const [
    { currentScriptUnitTest, currentScriptUnitTestIndex, scriptUnitTestResult },
    {
      setScriptUnitTestElementWithIndex,
      setPreviousScriptUnitTest,
      setNextScriptUnitTest,
      updateInputJson,
      updateExpectedOutputJson,
      setScriptUnitTestResult,
      resetScriptUnitTestResult,
      setCurrentScriptUnitTest,
      setCurrentScriptUnitTestIndex,
    },
  ] = useScriptUnitTestsState({ getScriptUnitTestElements });

  useEffect(() => {
    if (!scriptEditorState) {
      return;
    }
    setScriptUnitTestElementWithIndex(0, scriptEditorState.element);
  }, [scriptEditorState, setScriptUnitTestElementWithIndex]);

  const handleScriptEditorClose = () => {
    closeScriptEditorWithUpdate(
      scriptEventBus,
      scriptType,
      scriptText,
      scriptElement,
      closeScriptEditor,
      resetUnitTextResult,
    );
  };

  const handleEditorScriptTestUnitInputChange = (value: any) => {
    updateInputJson(value, scriptElement, scriptModeling);
  };

  const handleEditorScriptTestUnitOutputChange = (value: any) => {
    updateExpectedOutputJson(value, scriptElement, scriptModeling);
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
    runScriptUnitTest({
      currentScriptUnitTest,
      scriptElement,
      scriptText,
      beforeRun: resetUnitTextResult,
      onResult: processScriptUnitTestRunResult,
      onInvalidJson: () => {
        setScriptUnitTestResult({
          result: false,
          error: t('diagram_errors_json_formatting'),
        });
      },
      runRequest: (payload) => {
        return new Promise((resolve, reject) => {
          HttpService.makeCallToBackend({
            path: `/process-models/${modifiedProcessModelId}/script-unit-tests/run`,
            httpMethod: 'POST',
            successCallback: resolve,
            failureCallback: reject,
            postBody: payload,
          });
        });
      },
    });
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
      <ScriptAssistPanel
        value={scriptAssistValue}
        onChange={setScriptAssistValue}
        placeholder={t('diagram_script_assist_placeholder')}
        error={scriptAssistError}
        loading={scriptAssistLoading}
        buttonLabel={t('diagram_script_assist_button')}
        onSubmit={handleProcessScriptAssist}
      />
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
      <ScriptEditorDialog
        open={!!scriptEditorState}
        title={t('diagram_script_editor_title', { scriptName })}
        tabValue={scriptEditorTabValue}
        onTabChange={handleTabChange}
        scriptTabLabel={t('diagram_script_editor_tab_script_editor')}
        assistTabLabel={t('diagram_script_editor_tab_script_assist')}
        unitTestsTabLabel={t('diagram_script_editor_tab_unit_tests')}
        assistEnabled={scriptAssistEnabled ?? false}
        renderScript={scriptEditor}
        renderUnitTests={scriptUnitTestEditorElement}
        renderAssist={scriptEditorWithAssist}
        closeLabel={t('close')}
        onClose={handleScriptEditorClose}
      />
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
      <MarkdownEditorDialog
        open={!!markdownEditorState}
        onClose={handleMarkdownEditorClose}
        title={t('diagram_markdown_editor_title')}
        closeLabel={t('close')}
        renderEditor={() => (
          <MDEditor
            height={500}
            highlightEnable={false}
            value={markdownText}
            onChange={(value) => setMarkdownText(value || '')}
            components={{
              textarea: markdownEditorTextArea,
            }}
          />
        )}
      />
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
      <MessageEditorDialog
        open={!!messageEditorState}
        onClose={handleMessageEditorClose}
        onSave={handleMessageEditorSave}
        title={t('diagram_message_editor_title')}
        description={t('diagram_message_editor_description')}
        saveLabel={t('diagram_message_editor_save')}
        closeLabel={t('diagram_message_editor_close')}
        renderEditor={() => (
          <MessageEditor
            modifiedProcessGroupIdentifier={getGroupFromModifiedModelId(
              modifiedProcessModelId,
            )}
            messageId={messageEditorState.messageId}
            correlationProperties={messageEditorState.correlationProperties}
            messageEvent={messageEditorState.event}
            elementId={messageEditorState.elementId}
          />
        )}
      />
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
      <ProcessSearchDialog
        open={!!processSearchState}
        title={t('diagram_process_model_selector_title')}
        onChange={processSearchOnClose}
        processes={processes}
        titleText={t('diagram_process_model_selector_search_placeholder')}
        placeholderText={t('choose_a_process')}
      />
    );
  };

  const { onLaunchBpmnEditor, onLaunchDmnEditor } =
    useDiagramNavigationHandlers({
      processes,
      refreshProcesses,
      processModel,
      currentProcessModelId: params.process_model_id || '',
      normalizeProcessModelId: modifyProcessIdentifierForPathParam,
      pushNavigation,
      navigateTo: navigate,
      buildProcessFilePath,
      buildDmnListPath: (processModelId) =>
        generatePath('/process-models/:process_model_id/files', {
          process_model_id: processModelId || null,
        }) + '?file_type=dmn',
    });

  const onLaunchJsonSchemaEditor = useCallback(
    (element: any, fileName: string, eventBus: any) => {
      const url = import.meta.env.VITE_SPIFFWORKFLOW_FRONTEND_LAUNCH_EDITOR_URL;
      if (url) {
        window.open(
          `${url}?processModelId=${modifiedProcessModelId || ''}&fileName=${fileName || ''}`,
          '_blank',
        );
        return;
      }
      launchJsonSchemaEditor(element, fileName, eventBus);
    },
    [launchJsonSchemaEditor, modifiedProcessModelId],
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
      <JsonSchemaEditorDialog
        open={!!jsonSchemaEditorState}
        onClose={handleJsonSchemaEditorClose}
        title={t('diagram_json_schema_editor_title')}
        closeLabel={t('close')}
        renderEditor={() => (
          <ReactFormBuilder
            modifiedProcessModelId={modifiedProcessModelId || ''}
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
        )}
      />
    );
  };

  // onLaunchBpmnEditor/onLaunchDmnEditor now provided by useDiagramNavigationHandlers

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
          modifiedProcessModelId={modifiedProcessModelId || ''}
          saveDiagram={saveDiagram}
          navigationStack={navigationStack}
          onNavigate={(index) => {
            const item = navigationStack[index];
            if (!item) {
              return;
            }
            popToIndex(index);
            navigate(buildProcessFilePath(item));
          }}
        />
      );
    }
    // let this be undefined (so we won't display the button) unless the
    // current primary_file_name is different from the one we're looking at.
    let onSetPrimaryFileCallback;
    if (
      processModel &&
      params.file_name &&
      params.file_name !== processModel.primary_file_name &&
      modifyProcessIdentifierForPathParam(processModel.id) ===
        modifiedProcessModelId
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
        onJsonSchemaFilesRequested={
          bpmnEditorCallbacks.onJsonSchemaFilesRequested
        }
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
        modifiedProcessModelId={modifiedProcessModelId || ''}
        saveDiagram={saveDiagram}
        navigationStack={navigationStack}
        onNavigate={(index) => {
          const item = navigationStack[index];
          if (!item) {
            return;
          }
          popToIndex(index);
          navigate(buildProcessFilePath(item));
        }}
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
          ]}
        />

        {pageModals()}

        {unsavedChangesMessage()}
        {saveFileMessage()}
        {appropriateEditor()}
      </>
    );
  }
  return null;
}
