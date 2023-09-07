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
} from '@carbon/react';
import {
  SkipForward,
  SkipBack,
  PlayOutline,
  Close,
  Checkmark,
} from '@carbon/icons-react';

import Editor, { DiffEditor } from '@monaco-editor/react';

import MDEditor from '@uiw/react-md-editor';
import HttpService from '../services/HttpService';
import ReactDiagramEditor from '../components/ReactDiagramEditor';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import useAPIError from '../hooks/UseApiError';
import { makeid, modifyProcessIdentifierForPathParam } from '../helpers';
import {
  CarbonComboBoxProcessSelection,
  ProcessFile,
  ProcessModel,
  ProcessModelCaller,
  ProcessReference,
} from '../interfaces';
import ProcessSearch from '../components/ProcessSearch';
import { Notification } from '../components/Notification';
import { usePrompt } from '../hooks/UsePrompt';
import ActiveUsers from '../components/ActiveUsers';

export default function ProcessModelEditDiagram() {
  const [showFileNameEditor, setShowFileNameEditor] = useState(false);
  const handleShowFileNameEditor = () => setShowFileNameEditor(true);
  const [processModel, setProcessModel] = useState<ProcessModel | null>(null);
  const [diagramHasChanges, setDiagramHasChanges] = useState<boolean>(false);

  const [scriptText, setScriptText] = useState<string>('');
  const [scriptType, setScriptType] = useState<string>('');
  const [scriptEventBus, setScriptEventBus] = useState<any>(null);
  const [scriptModeling, setScriptModeling] = useState(null);
  const [scriptElement, setScriptElement] = useState(null);
  const [showScriptEditor, setShowScriptEditor] = useState(false);
  const handleShowScriptEditor = () => setShowScriptEditor(true);

  const [markdownText, setMarkdownText] = useState<string | undefined>('');
  const [markdownEventBus, setMarkdownEventBus] = useState<any>(null);
  const [showMarkdownEditor, setShowMarkdownEditor] = useState(false);
  const [showProcessSearch, setShowProcessSearch] = useState(false);
  const [processSearchEventBus, setProcessSearchEventBus] = useState<any>(null);
  const [processSearchElement, setProcessSearchElement] = useState<any>(null);
  const [processes, setProcesses] = useState<ProcessReference[]>([]);
  const [displaySaveFileMessage, setDisplaySaveFileMessage] =
    useState<boolean>(false);
  const [processModelFileInvalidText, setProcessModelFileInvalidText] =
    useState<string>('');

  const handleShowMarkdownEditor = () => setShowMarkdownEditor(true);

  const editorRef = useRef(null);
  const monacoRef = useRef(null);

  const failingScriptLineClassNamePrefix = 'failingScriptLineError';

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
    null
  );
  const [newFileName, setNewFileName] = useState('');
  const [bpmnXmlForDiagramRendering, setBpmnXmlForDiagramRendering] =
    useState(null);

  const modifiedProcessModelId = modifyProcessIdentifierForPathParam(
    (params as any).process_model_id
  );

  const processModelPath = `process-models/${modifiedProcessModelId}`;

  const [callers, setCallers] = useState<ProcessModelCaller[]>([]);

  usePrompt('Changes you made may not be saved.', diagramHasChanges);

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
      successCallback: setProcessModel,
    });

    if (params.file_name) {
      HttpService.makeCallToBackend({
        path: `/${processModelPath}/files/${params.file_name}`,
        successCallback: fileResult,
      });
    }
  }, [processModelPath, params]);

  useEffect(() => {
    const bpmnProcessIds = processModelFile?.bpmn_process_ids;
    if (processModel !== null && bpmnProcessIds) {
      HttpService.makeCallToBackend({
        path: `/processes/callers/${bpmnProcessIds.join(',')}`,
        successCallback: setCallers,
      });
    }
  }, [processModel, processModelFile]);

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
        'file_type'
      )}`;
      navigate(
        `/editor/process-models/${modifiedProcessModelId}/files/${fileNameWithExtension}`
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

  const onElementsChanged = () => {
    setDiagramHasChanges(true);
  };

  const onDeleteFile = (fileName = params.file_name) => {
    const url = `/process-models/${modifiedProcessModelId}/files/${fileName}`;
    const httpMethod = 'DELETE';

    const navigateToProcessModelShow = (_httpResult: any) => {
      navigate(`/admin/process-models/${modifiedProcessModelId}`);
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
      navigate(`/admin${url}`);
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
        modalHeading="Processs Model File Name"
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
        `^.${failingScriptLineClassNamePrefix}_.*::after `
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

  const onServiceTasksRequested = (event: any) => {
    HttpService.makeCallToBackend({
      path: `/service-tasks`,
      successCallback: makeApiHandler(event),
    });
  };

  const onJsonFilesRequested = (event: any) => {
    if (processModel) {
      const jsonFiles = processModel.files.filter((f) => f.type === 'json');
      const options = jsonFiles.map((f) => {
        return { label: f.name, value: f.name };
      });
      event.eventBus.fire('spiff.json_files.returned', { options });
    } else {
      console.error('There is no process Model.');
    }
  };

  const onDmnFilesRequested = (event: any) => {
    if (processModel) {
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
  };

  const getScriptUnitTestElements = (element: any) => {
    const { extensionElements } = element.businessObject;
    if (extensionElements && extensionElements.values.length > 0) {
      const unitTestModdleElements = extensionElements
        .get('values')
        .filter(function getInstanceOfType(e: any) {
          return e.$instanceOf('spiffworkflow:unitTests');
        })[0];
      if (unitTestModdleElements) {
        return unitTestModdleElements.unitTests;
      }
    }
    return [];
  };

  const setScriptUnitTestElementWithIndex = (
    scriptIndex: number,
    element: any = scriptElement
  ) => {
    const unitTestsModdleElements = getScriptUnitTestElements(element);
    if (unitTestsModdleElements.length > 0) {
      setCurrentScriptUnitTest(unitTestsModdleElements[scriptIndex]);
      setCurrentScriptUnitTestIndex(scriptIndex);
    }
  };

  const onLaunchScriptEditor = (
    element: any,
    script: string,
    scriptTypeString: string,
    eventBus: any,
    modeling: any
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
  };

  const handleScriptEditorClose = () => {
    scriptEventBus.fire('spiff.script.update', {
      scriptType,
      script: scriptText,
      element: scriptElement,
    });

    resetUnitTextResult();
    setShowScriptEditor(false);
  };

  const handleEditorScriptChange = (value: any) => {
    setScriptText(value);
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
      setScriptUnitTestElementWithIndex(newScriptIndex);
    }
  };

  const setNextScriptUnitTest = () => {
    resetUnitTextResult();
    const newScriptIndex = currentScriptUnitTestIndex + 1;
    const unitTestsModdleElements = getScriptUnitTestElements(scriptElement);
    if (newScriptIndex < unitTestsModdleElements.length) {
      setScriptUnitTestElementWithIndex(newScriptIndex);
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
          7
        )}`;

        // document.documentElement.style.setProperty causes the content property to go away
        // so add the rule dynamically instead of changing a property variable
        document.styleSheets[0].addRule(
          `.${currentClassName}::after`,
          `content: "  # ${result.error.replaceAll('"', '')}"; color: red`
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
                lineLength
              ),
              options: { afterContentClassName: currentClassName },
            },
          ]
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
          currentScriptUnitTest.expectedOutputJson.value
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
          scriptUnitTestResult.error
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
            '  '
          );
        }
        const contextJson = JSON.stringify(
          scriptUnitTestResult.context,
          null,
          '  '
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
          '  '
        );
        outputJson = JSON.stringify(
          JSON.parse(currentScriptUnitTest.expectedOutputJson.value),
          null,
          '  '
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
                  value={inputJson}
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
                  value={outputJson}
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
  const scriptEditor = () => {
    return (
      <Editor
        height={500}
        width="auto"
        options={generalEditorOptions()}
        defaultLanguage="python"
        value={scriptText}
        onChange={handleEditorScriptChange}
        onMount={handleEditorDidMount}
      />
    );
  };
  const scriptEditorAndTests = () => {
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
            <Tab>Unit Tests</Tab>
          </TabList>
          <TabPanels>
            <TabPanel>{scriptEditor()}</TabPanel>
            <TabPanel>{scriptUnitTestEditorElement()}</TabPanel>
          </TabPanels>
        </Tabs>
      </Modal>
    );
  };
  const onLaunchMarkdownEditor = (
    _element: any,
    markdown: string,
    eventBus: any
  ) => {
    setMarkdownText(markdown || '');
    setMarkdownEventBus(eventBus);
    handleShowMarkdownEditor();
  };
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

  const onSearchProcessModels = (
    _processId: string,
    eventBus: any,
    element: any
  ) => {
    setProcessSearchEventBus(eventBus);
    setProcessSearchElement(element);
    setShowProcessSearch(true);
  };
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

  const findFileNameForReferenceId = (
    id: string,
    type: string
  ): ProcessFile | null => {
    // Given a reference id (like a process_id, or decision_id) finds the file
    // that contains that reference and returns it.
    let matchFile = null;
    if (processModel) {
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
  };

  const onLaunchBpmnEditor = (processId: string) => {
    const openProcessModelFileInNewTab = (
      processReference: ProcessReference
    ) => {
      const path = generatePath(
        '/editor/process-models/:process_model_path/files/:file_name',
        {
          process_model_path: modifyProcessIdentifierForPathParam(
            processReference.process_model_id
          ),
          file_name: processReference.file_name,
        }
      );
      window.open(path);
    };

    const openFileNameForProcessId = (
      processesReferences: ProcessReference[]
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
  };

  const onLaunchJsonEditor = (fileName: string) => {
    const path = generatePath(
      '/admin/process-models/:process_model_id/form/:file_name',
      {
        process_model_id: params.process_model_id,
        file_name: fileName,
      }
    );
    window.open(path);
  };
  const onLaunchDmnEditor = (processId: string) => {
    const file = findFileNameForReferenceId(processId, 'dmn');
    if (file) {
      const path = generatePath(
        '/editor/process-models/:process_model_id/files/:file_name',
        {
          process_model_id: params.process_model_id,
          file_name: file.name,
        }
      );
      window.open(path);
    }
  };

  const isDmn = () => {
    const fileName = params.file_name || '';
    return searchParams.get('file_type') === 'dmn' || fileName.endsWith('.dmn');
  };

  const appropriateEditor = () => {
    if (isDmn()) {
      return (
        <ReactDiagramEditor
          processModelId={params.process_model_id || ''}
          saveDiagram={saveDiagram}
          onDeleteFile={onDeleteFile}
          diagramXML={bpmnXmlForDiagramRendering}
          fileName={params.file_name}
          diagramType="dmn"
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
        processModelId={params.process_model_id || ''}
        saveDiagram={saveDiagram}
        onDeleteFile={onDeleteFile}
        isPrimaryFile={params.file_name === processModel?.primary_file_name}
        onSetPrimaryFile={onSetPrimaryFileCallback}
        diagramXML={bpmnXmlForDiagramRendering}
        fileName={params.file_name}
        diagramType="bpmn"
        onLaunchScriptEditor={onLaunchScriptEditor}
        onServiceTasksRequested={onServiceTasksRequested}
        onLaunchMarkdownEditor={onLaunchMarkdownEditor}
        onLaunchBpmnEditor={onLaunchBpmnEditor}
        onLaunchJsonEditor={onLaunchJsonEditor}
        onJsonFilesRequested={onJsonFilesRequested}
        onLaunchDmnEditor={onLaunchDmnEditor}
        onDmnFilesRequested={onDmnFilesRequested}
        onSearchProcessModels={onSearchProcessModels}
        onElementsChanged={onElementsChanged}
        callers={callers}
        activeUserElement={<ActiveUsers />}
      />
    );
  };

  const saveFileMessage = () => {
    if (displaySaveFileMessage) {
      return (
        <Notification
          title="File Saved: "
          onClose={() => setDisplaySaveFileMessage(false)}
        >
          Changes to the file were saved.
        </Notification>
      );
    }
    return null;
  };

  // if a file name is not given then this is a new model and the ReactDiagramEditor component will handle it
  if ((bpmnXmlForDiagramRendering || !params.file_name) && processModel) {
    const processModelFileName = processModelFile ? processModelFile.name : '';
    return (
      <>
        <ProcessBreadcrumb
          hotCrumbs={[
            ['Process Groups', '/admin'],
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
        {saveFileMessage()}
        {appropriateEditor()}
        {newFileNameBox()}
        {scriptEditorAndTests()}
        {markdownEditor()}
        {processModelSelector()}
        <div id="diagram-container" />
      </>
    );
  }
  return null;
}
