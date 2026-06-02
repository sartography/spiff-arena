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

import ThemedCodeMirror from '../components/ThemedCodeMirror';
import ThemedCodeMirrorMerge from '../components/ThemedCodeMirrorMerge';
import { python } from '@codemirror/lang-python';
import { json } from '@codemirror/lang-json';
import { indentUnit } from '@codemirror/language';
import { EditorView, Decoration, type DecorationSet } from '@codemirror/view';
import { EditorState, StateField, StateEffect } from '@codemirror/state';

import { Can } from '@casl/react';
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
  MarkdownEditorDialog,
  JsonSchemaEditorDialog,
  FileNameEditorDialog,
  ProcessSearchDialog,
  ScriptAssistPanel,
  ScriptEditorDialog,
  useDiagramNavigationStack,
  useDiagramNavigationHandlers,
  closeMarkdownEditorWithUpdate,
  closeJsonSchemaEditorWithUpdate,
  closeScriptEditorWithUpdate,
} from '../../packages/bpmn-js-spiffworkflow-react/src';
import type { DiagramNavigationItem } from '../../packages/bpmn-js-spiffworkflow-react/src';
import { spiffBpmnApiService } from '../services/SpiffBpmnApiService';
import {
  modifyProcessIdentifierForPathParam,
  setPageTitle,
  unModifyProcessIdentifierForPathParam,
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
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import { usePermissionFetcher } from '../hooks/PermissionService';

// State effects for managing error line decorations in script editor
const addErrorLineEffect = StateEffect.define<{
  line: number;
  error: string;
}>();
const clearErrorLineEffect = StateEffect.define<null>();

// State field to track error line decorations
const errorLineField = StateField.define<DecorationSet>({
  create() {
    return Decoration.none;
  },
  update(decorations, tr) {
    decorations = decorations.map(tr.changes);
    for (const effect of tr.effects) {
      if (effect.is(addErrorLineEffect)) {
        const { line: lineNumber, error } = effect.value;
        try {
          const line = tr.state.doc.line(lineNumber);
          const decoration = Decoration.line({
            attributes: {
              class: 'cm-script-error-line',
              'data-error': error,
            },
          });
          decorations = Decoration.set([decoration.range(line.from)]);
        } catch (e) {
          console.error('Failed to add error decoration:', e);
        }
      } else if (effect.is(clearErrorLineEffect)) {
        decorations = Decoration.none;
      }
    }
    return decorations;
  },
  provide: (field) => EditorView.decorations.from(field),
});

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

  // CodeMirror editor reference for script unit test error highlighting
  const scriptEditorViewRef = useRef<EditorView | null>(null);
  // Persist error info to apply when editor is created (survives tab switches)
  const [scriptErrorInfo, setScriptErrorInfo] = useState<{
    line: number;
    error: string;
  } | null>(null);

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
  const {
    onLaunchScriptEditor,
    onLaunchMarkdownEditor,
    onLaunchJsonSchemaEditor: launchJsonSchemaEditor,
    onSearchProcessModels,
    scriptEditorState,
    markdownEditorState,
    jsonSchemaEditorState,
    processSearchState,
    closeScriptEditor,
    closeMarkdownEditor,
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

  const params = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  // CRITICAL: params.process_model_id is ALREADY colon-separated from URL!
  const modifiedProcessModelId = params.process_model_id || '';

  // Navigate to the Messages page to edit a message model rather than opening
  // an inline modal. This makes it clear the message is a shared resource.
  const onLaunchMessageEditor = useCallback(
    (event: any) => {
      const messageId = event?.value?.messageId;
      if (messageId) {
        const nextSearchParams = new URLSearchParams({
          message_id: messageId,
          tab: 'models',
        });
        const sourceLocation = unModifyProcessIdentifierForPathParam(
          modifiedProcessModelId,
        );
        if (sourceLocation) {
          nextSearchParams.set('source_location', sourceLocation);
        }
        window.open(`/messages?${nextSearchParams.toString()}`, '_blank');
      } else {
        window.open('/messages?tab=models', '_blank');
      }
    },
    [modifiedProcessModelId],
  );

  const { addError, removeError } = useAPIError();
  const [processModelFile, setProcessModelFile] = useState<ProcessFile | null>(
    null,
  );
  const [newFileName, setNewFileName] = useState('');
  const [bpmnXmlForDiagramRendering, setBpmnXmlForDiagramRendering] =
    useState(null);

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
    // Clear error state
    setScriptErrorInfo(null);
    // Clear any error line decorations in the editor
    if (scriptEditorViewRef.current) {
      scriptEditorViewRef.current.dispatch({
        effects: clearErrorLineEffect.of(null),
      });
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

  const processScriptUnitTestRunResult = (result: any) => {
    if ('result' in result) {
      setScriptUnitTestResult(result);
      // Store error info for highlighting (will be applied when editor is created/visible)
      if (result.line_number && result.error) {
        // Ensure CSS styles are present
        if (!document.getElementById('cm-script-error-styles')) {
          const style = document.createElement('style');
          style.id = 'cm-script-error-styles';
          style.textContent = `
            .cm-script-error-line {
              background-color: rgba(255, 0, 0, 0.1) !important;
              border-left: 3px solid red !important;
            }
            .cm-script-error-line::after {
              content: "  # " attr(data-error);
              color: red;
              font-style: italic;
            }
          `;
          document.head.appendChild(style);
        }

        // Store error info to persist across tab switches
        setScriptErrorInfo({
          line: result.line_number,
          error: result.error,
        });

        // If editor is currently mounted, apply decoration immediately
        if (scriptEditorViewRef.current) {
          scriptEditorViewRef.current.dispatch({
            effects: addErrorLineEffect.of({
              line: result.line_number,
              error: result.error,
            }),
          });
        }
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
          <ThemedCodeMirrorMerge style={{ height: '200px' }}>
            <ThemedCodeMirrorMerge.Original
              value={outputJson}
              extensions={[json()]}
            />
            <ThemedCodeMirrorMerge.Modified
              value={contextJson}
              extensions={[
                json(),
                EditorView.editable.of(false),
                EditorState.readOnly.of(true),
              ]}
            />
          </ThemedCodeMirrorMerge>
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
                <ThemedCodeMirror
                  height={'500px'}
                  value={inputJson}
                  extensions={[json()]}
                  onChange={handleEditorScriptTestUnitInputChange}
                />
              </div>
            </Grid>
            <Grid size={{ xs: 6 }}>
              <div>
                {t('diagram_script_editor_unit_test_expected_output_json')}
              </div>
              <div>
                <ThemedCodeMirror
                  height={'500px'}
                  value={outputJson}
                  extensions={[json()]}
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
    const handleEditorCreate = (view: EditorView) => {
      scriptEditorViewRef.current = view;

      // Apply error decoration if there's a pending error from unit test
      if (scriptErrorInfo) {
        // Use setTimeout to ensure the editor is fully initialized
        setTimeout(() => {
          if (view && scriptErrorInfo) {
            view.dispatch({
              effects: addErrorLineEffect.of({
                line: scriptErrorInfo.line,
                error: scriptErrorInfo.error,
              }),
            });
          }
        }, 0);
      }
    };

    return (
      <ThemedCodeMirror
        height={'500px'}
        value={scriptText}
        extensions={[python(), indentUnit.of('    '), errorLineField]}
        onChange={handleEditorScriptChange}
        onCreateEditor={handleEditorCreate}
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
            anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
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
