import { useCallback, useEffect, useRef, useState } from 'react';
import {
  generatePath,
  useNavigate,
  useParams,
  useSearchParams,
} from 'react-router-dom';
import {
  Button,
  ButtonSet,
  Modal,
  Tabs,
  TabList,
  Tab,
  TabPanels,
  TabPanel,
  TextInput,
  Grid,
  Column,
  Stack,
  TextArea,
  InlineLoading,
} from '@carbon/react';
import {
  SkipForward,
  SkipBack,
  PlayOutline,
  Close,
  Checkmark,
  Information,
} from '@carbon/icons-react';
import { gray } from '@carbon/colors';

import { Can } from '@casl/react';
import Editor, { DiffEditor } from '@monaco-editor/react';
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
  CarbonComboBoxProcessSelection,
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
import SpiffTooltip from '../components/SpiffTooltip';
import { MessageEditor } from '../components/messages/MessageEditor';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import { usePermissionFetcher } from '../hooks/PermissionService';

export default function ProcessModelEditDiagram() {
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
        `/editor/process-models/${modifiedProcessModelId}/files/${fileNameWithExtension}`,
      );
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
      setProcessModelFileInvalidText('Process Model file name is required.');
      return;
    }
    setProcessModelFileInvalidText('');
    setShowFileNameEditor(false);
    saveDiagram(bpmnXmlForDiagramRendering);
  };

  const newFileNameBox = () => {
    const fileExtension = `.${searchParams.get('file_type')}`;
    return (
      <Modal
        open={showFileNameEditor}
        modalHeading="Process Model File Name"
        primaryButtonText="Save Changes"
        secondaryButtonText="Cancel"
        onSecondarySubmit={handleFileNameCancel}
        onRequestSubmit={handleFileNameSave}
        onRequestClose={handleFileNameCancel}
      >
        <Grid
          condensed
          fullWidth
          className="megacondensed process-model-files-section"
        >
          <Column md={4} lg={8} sm={4}>
            <TextInput
              id="process_model_file_name"
              labelText="File Name:"
              value={newFileName}
              onChange={(e: any) => setNewFileName(e.target.value)}
              invalidText={processModelFileInvalidText}
              invalid={!!processModelFileInvalidText}
              size="sm"
              autoFocus
            />
          </Column>
          <Column
            md={4}
            lg={8}
            sm={4}
            className="with-top-margin-for-label-next-to-text-input"
          >
            {fileExtension}
          </Column>
        </Grid>
      </Modal>
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
      } catch (e) {
        setScriptUnitTestResult({
          result: false,
          error: 'The JSON provided contains a formatting error.',
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
        errorObject = 'Unexpected result. Please see the comparison below.';
      } else if (scriptUnitTestResult.line_number) {
        errorObject = `Error encountered running the script.  Please check the code around line ${scriptUnitTestResult.line_number}`;
      } else {
        errorObject = `Error encountered running the script. ${JSON.stringify(
          scriptUnitTestResult.error,
        )}`;
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
              <Button
                kind="ghost"
                className="green-icon"
                renderIcon={Checkmark}
                iconDescription="Unit tests passed"
                hasIconOnly
                size="lg"
              />
            )}
            {scriptUnitTestResult.result === false && (
              <Button
                kind="ghost"
                className="red-icon"
                renderIcon={Close}
                iconDescription="Unit tests failed"
                hasIconOnly
                size="lg"
              />
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
      } catch (e) {
        // Attemping to format the json failed -- it's invalid.
      }

      return (
        <main>
          <Grid condensed fullWidth>
            <Column md={4} lg={8} sm={2}>
              <p className="with-top-margin-for-unit-test-name">
                Unit Test: {currentScriptUnitTest.id}
              </p>
            </Column>
            <Column md={4} lg={8} sm={2}>
              <ButtonSet>
                <Button
                  kind="ghost"
                  data-qa="unit-test-previous-button"
                  renderIcon={SkipBack}
                  iconDescription="Previous Unit Test"
                  hasIconOnly
                  size="lg"
                  disabled={previousButtonDisable}
                  onClick={setPreviousScriptUnitTest}
                />
                <Button
                  kind="ghost"
                  data-qa="unit-test-next-button"
                  renderIcon={SkipForward}
                  iconDescription="Next Unit Test"
                  hasIconOnly
                  size="lg"
                  disabled={nextButtonDisable}
                  onClick={setNextScriptUnitTest}
                />
                <Button
                  kind="ghost"
                  data-qa="unit-test-run"
                  renderIcon={PlayOutline}
                  iconDescription="Run Unit Test"
                  hasIconOnly
                  size="lg"
                  onClick={runCurrentUnitTest}
                />
                {scriptUnitTestResultBoolElement}
              </ButtonSet>
            </Column>
          </Grid>
          <Grid condensed fullWidth>
            <Column md={8} lg={16} sm={4}>
              {unitTestFailureElement()}
            </Column>
          </Grid>
          <Grid condensed fullWidth>
            <Column md={4} lg={8} sm={2}>
              <div>Input Json:</div>
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
            </Column>
            <Column md={4} lg={8} sm={2}>
              <div>Expected Output Json:</div>
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
            </Column>
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
        setScriptAssistError(`Failed to process script assist query: ${error}`);
      }
    } else {
      setScriptAssistError('Please provide instructions for your script!');
    }
  };

  /* If the Script Assist tab is enabled (via scriptAssistEnabled), this is the UI */
  const scriptAssistWindow = () => {
    return (
      <>
        <TextArea
          placeholder="Ask Spiff AI"
          rows={20}
          value={scriptAssistValue}
          onChange={(e: any) => setScriptAssistValue(e.target.value)}
        />
        <Stack
          className="flex-justify-end flex-align-horizontal-center"
          orientation="horizontal"
          gap={5}
        >
          {scriptAssistError && (
            <div className="error-text-red">{scriptAssistError}</div>
          )}
          {scriptAssistLoading && (
            <InlineLoading
              status="active"
              iconDescription="Loading"
              description="Fetching script..."
            />
          )}
          <Button
            className="m-top-10"
            kind="primary"
            onClick={() => handleProcessScriptAssist()}
            disabled={scriptAssistLoading}
          >
            Ask Spiff AI
          </Button>
        </Stack>
      </>
    );
  };

  const scriptEditor = () => {
    return (
      <Grid fullwidth>
        <Column lg={16} md={8} sm={4}>
          {editorWindow()}
        </Column>
      </Grid>
    );
  };

  const scriptEditorWithAssist = () => {
    return (
      <Grid fullwidth>
        <Column lg={10} md={4} sm={2}>
          {editorWindow()}
        </Column>
        <Column lg={6} md={4} sm={2}>
          <Stack
            gap={3}
            orientation="horizontal"
            className="stack-align-content-horizontal p-bottom-10"
            color={gray[50]}
          >
            <SpiffTooltip title="Use natural language to create your script. Hint: start basic and edit to tweak.">
              <Stack className="gray-text flex-align-horizontal-center">
                <Information size={14} />
                <Stack className="p-left-10 not-editable">
                  Create a python script that...
                </Stack>
              </Stack>
            </SpiffTooltip>
          </Stack>
          {scriptAssistWindow()}
        </Column>
      </Grid>
    );
  };

  const scriptEditorAndTests = () => {
    if (!showScriptEditor) {
      return null;
    }
    let scriptName = '';
    if (scriptElement) {
      scriptName = (scriptElement as any).di.bpmnElement.name;
    }
    return (
      <Modal
        open={showScriptEditor}
        modalHeading={`Editing Script: ${scriptName}`}
        primaryButtonText="Close"
        onRequestSubmit={handleScriptEditorClose}
        size="lg"
        onRequestClose={handleScriptEditorClose}
      >
        <Tabs>
          <TabList aria-label="List of tabs" activation="manual">
            <Tab>Script Editor</Tab>
            {scriptAssistEnabled && <Tab>Script Assist</Tab>}
            <Tab>Unit Tests</Tab>
          </TabList>
          <TabPanels>
            <TabPanel>{scriptEditor()}</TabPanel>
            {scriptAssistEnabled && (
              <TabPanel>{scriptEditorWithAssist()}</TabPanel>
            )}
            <TabPanel>{scriptUnitTestEditorElement()}</TabPanel>
          </TabPanels>
        </Tabs>
      </Modal>
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

  const markdownEditor = () => {
    return (
      <Modal
        open={showMarkdownEditor}
        modalHeading="Edit Markdown"
        primaryButtonText="Close"
        onRequestSubmit={handleMarkdownEditorClose}
        onRequestClose={handleMarkdownEditorClose}
        size="lg"
      >
        <div data-color-mode="light">
          <MDEditor
            height={500}
            highlightEnable={false}
            value={markdownText}
            onChange={setMarkdownText}
          />
        </div>
      </Modal>
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
      <Modal
        open={showMessageEditor}
        modalHeading="Message Editor"
        modalLabel="Create or edit a message and manage its correlation properties"
        primaryButtonText="Save"
        secondaryButtonText="Close (this does not save)"
        onRequestSubmit={handleMessageEditorSave}
        onRequestClose={handleMessageEditorClose}
        size="lg"
        preventCloseOnClickOutside
        primaryButtonKind="primary"
      >
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
      </Modal>
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
  const processSearchOnClose = (selection: CarbonComboBoxProcessSelection) => {
    const selectedProcessModel = selection.selectedItem;
    if (selectedProcessModel) {
      processSearchEventBus.fire('spiff.callactivity.update', {
        element: processSearchElement,
        value: selectedProcessModel.identifier,
      });
    }
    setShowProcessSearch(false);
  };

  const processModelSelector = () => {
    return (
      <Modal
        open={showProcessSearch}
        modalHeading="Select Process Model"
        primaryButtonText="Close"
        onRequestClose={processSearchOnClose}
        onRequestSubmit={processSearchOnClose}
        size="lg"
      >
        <ProcessSearch
          height="500px"
          onChange={processSearchOnClose}
          processes={processes}
          titleText="Process model search"
        />
      </Modal>
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
          '/editor/process-models/:process_model_path/files/:file_name',
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
      <Modal
        open={showJsonSchemaEditor}
        modalHeading="Edit JSON Schema"
        primaryButtonText="Close"
        onRequestSubmit={handleJsonSchemaEditorClose}
        onRequestClose={handleJsonSchemaEditorClose}
        size="lg"
      >
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
        />
      </Modal>
    );
  };

  const onLaunchDmnEditor = useCallback(
    (processId: string) => {
      const file = findFileNameForReferenceId(processId, 'dmn');
      let path = '';
      if (file) {
        path = generatePath(
          '/editor/process-models/:process_model_id/files/:file_name',
          {
            process_model_id: params.process_model_id || null,
            file_name: file.name,
          },
        );
        window.open(path);
      } else {
        path = generatePath(
          '/editor/process-models/:process_model_id/files?file_type=dmn',
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
          title="File Saved: "
          onClose={() => setDisplaySaveFileMessage(false)}
          hideCloseButton
          timeout={3000}
        >
          Changes to the file were saved.
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
            title="Unsaved changes."
            type="error"
            hideCloseButton
            data-qa="process-model-file-changed"
          >
            Please save to avoid losing your work.
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
            ['Process Groups', '/process-groups'],
            {
              entityToExplode: processModel,
              entityType: 'process-model',
              linkLastItem: true,
            },
            [processModelFileName],
          ]}
        />
        <h1>
          Process Model File{processModelFile ? ': ' : ''}
          {processModelFileName}
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
