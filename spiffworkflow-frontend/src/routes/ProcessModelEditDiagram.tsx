import { useContext, useEffect, useRef, useState } from 'react';
import {
  generatePath,
  useNavigate,
  useParams,
  useSearchParams,
} from 'react-router-dom';
// @ts-ignore
import { Button, Modal, Stack, Content } from '@carbon/react';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';

import Editor from '@monaco-editor/react';

import MDEditor from '@uiw/react-md-editor';
import ReactDiagramEditor from '../components/ReactDiagramEditor';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import HttpService from '../services/HttpService';
import ErrorContext from '../contexts/ErrorContext';
import { makeid, modifyProcessModelPath } from '../helpers';
import { ProcessFile, ProcessModel } from '../interfaces';

export default function ProcessModelEditDiagram() {
  const [showFileNameEditor, setShowFileNameEditor] = useState(false);
  const handleShowFileNameEditor = () => setShowFileNameEditor(true);
  const [processModel, setProcessModel] = useState<ProcessModel | null>(null);

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
    context: object;
    error: string;
    line_number: number;
    offset: number;
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

  const setErrorMessage = (useContext as any)(ErrorContext)[1];
  const [processModelFile, setProcessModelFile] = useState(null);
  const [newFileName, setNewFileName] = useState('');
  const [bpmnXmlForDiagramRendering, setBpmnXmlForDiagramRendering] =
    useState(null);

  const modifiedProcessModelId = modifyProcessModelPath(
    (params as any).process_model_id
  );

  const processModelPath = `process-models/${modifiedProcessModelId}`;

  useEffect(() => {
    const processResult = (result: ProcessModel) => {
      setProcessModel(result);
    };
    HttpService.makeCallToBackend({
      path: `/${processModelPath}`,
      successCallback: processResult,
    });
  }, [processModelPath]);

  useEffect(() => {
    const fileResult = (result: any) => {
      setProcessModelFile(result);
      setBpmnXmlForDiagramRendering(result.file_contents);
    };

    if (params.file_name) {
      console.log(`processModelPath: ${processModelPath}`);
      HttpService.makeCallToBackend({
        path: `/${processModelPath}/files/${params.file_name}`,
        successCallback: fileResult,
      });
    }
  }, [processModelPath, params]);

  const handleFileNameCancel = () => {
    setShowFileNameEditor(false);
    setNewFileName('');
  };

  const navigateToProcessModelFile = (_result: any) => {
    if (!params.file_name) {
      const fileNameWithExtension = `${newFileName}.${searchParams.get(
        'file_type'
      )}`;
      navigate(
        `/admin/process-models/${modifiedProcessModelId}/files/${fileNameWithExtension}`
      );
    }
  };

  const saveDiagram = (bpmnXML: any, fileName = params.file_name) => {
    setErrorMessage(null);
    setBpmnXmlForDiagramRendering(bpmnXML);

    let url = `/process-models/${modifiedProcessModelId}/files`;
    let httpMethod = 'PUT';
    let fileNameWithExtension = fileName;

    if (newFileName) {
      fileNameWithExtension = `${newFileName}.${searchParams.get('file_type')}`;
      httpMethod = 'POST';
    } else {
      url += `/${fileNameWithExtension}`;
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
      failureCallback: setErrorMessage,
      httpMethod,
      postBody: formData,
    });

    // after saving the file, make sure we null out newFileName
    // so it does not get used over the params
    setNewFileName('');
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
      >
        <label>File Name:</label>
        <span>
          <input
            name="file_name"
            type="text"
            value={newFileName}
            onChange={(e) => setNewFileName(e.target.value)}
            autoFocus
          />
          {fileExtension}
        </span>
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
      path: `/service_tasks`,
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
      console.log('There is no process Model.');
    }
  };

  const onDmnFilesRequested = (event: any) => {
    if (processModel) {
      const dmnFiles = processModel.files.filter((f) => f.type === 'dmn');
      const options: any[] = [];
      dmnFiles.forEach((file) => {
        file.references.forEach((ref) => {
          options.push({ label: ref.name, value: ref.id });
        });
      });
      console.log('Options', options);
      event.eventBus.fire('spiff.dmn_files.returned', { options });
    } else {
      console.log('There is no process model.');
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
      resetUnitTextResult();
      HttpService.makeCallToBackend({
        path: `/process-models/${modifiedProcessModelId}/script-unit-tests/run`,
        httpMethod: 'POST',
        successCallback: processScriptUnitTestRunResult,
        postBody: {
          bpmn_task_identifier: (scriptElement as any).id,
          python_script: scriptText,
          input_json: JSON.parse(currentScriptUnitTest.inputJson.value),
          expected_output_json: JSON.parse(
            currentScriptUnitTest.expectedOutputJson.value
          ),
        },
      });
    }
  };

  const unitTestFailureElement = () => {
    if (
      scriptUnitTestResult &&
      scriptUnitTestResult.result === false &&
      !scriptUnitTestResult.line_number
    ) {
      let errorStringElement = null;
      if (scriptUnitTestResult.error) {
        errorStringElement = (
          <span>
            Received error when running script:{' '}
            {JSON.stringify(scriptUnitTestResult.error)}
          </span>
        );
      }
      let errorContextElement = null;
      if (scriptUnitTestResult.context) {
        errorContextElement = (
          <span>
            Received unexpected output:{' '}
            {JSON.stringify(scriptUnitTestResult.context)}
          </span>
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
          <Col xs={1}>
            {scriptUnitTestResult.result === true && (
              <span style={{ color: 'green', fontSize: '3em' }}>✓</span>
            )}
            {scriptUnitTestResult.result === false && (
              <span style={{ color: 'red', fontSize: '3em' }}>✘</span>
            )}
          </Col>
        );
      }
      return (
        <main>
          <Content>
            <Row>
              <Col xs={8}>
                <Button variant="link" disabled style={{ fontSize: '1.5em' }}>
                  Unit Test: {currentScriptUnitTest.id}
                </Button>
              </Col>
              <Col xs={1}>
                <Button
                  data-qa="unit-test-previous-button"
                  style={{ fontSize: '1.5em' }}
                  onClick={setPreviousScriptUnitTest}
                  variant="link"
                  disabled={previousButtonDisable}
                >
                  &laquo;
                </Button>
              </Col>
              <Col xs={1}>
                <Button
                  data-qa="unit-test-next-button"
                  style={{ fontSize: '1.5em' }}
                  onClick={setNextScriptUnitTest}
                  variant="link"
                  disabled={nextButtonDisable}
                >
                  &raquo;
                </Button>
              </Col>
              <Col xs={1}>
                <Button
                  className="justify-content-end"
                  data-qa="unit-test-run"
                  style={{ fontSize: '1.5em' }}
                  onClick={runCurrentUnitTest}
                >
                  Run
                </Button>
              </Col>
              <Col xs={1}>{scriptUnitTestResultBoolElement}</Col>
            </Row>
          </Content>
          <Stack orientation="horizontal" gap={3}>
            {unitTestFailureElement()}
          </Stack>
          <Stack orientation="horizontal" gap={3}>
            <Stack>
              <div>Input Json:</div>
              <div>
                <Editor
                  height={200}
                  defaultLanguage="json"
                  options={Object.assign(generalEditorOptions(), {
                    minimap: { enabled: false },
                  })}
                  value={currentScriptUnitTest.inputJson.value}
                  onChange={handleEditorScriptTestUnitInputChange}
                />
              </div>
            </Stack>
            <Stack>
              <div>Expected Output Json:</div>
              <div>
                <Editor
                  height={200}
                  defaultLanguage="json"
                  options={Object.assign(generalEditorOptions(), {
                    minimap: { enabled: false },
                  })}
                  value={currentScriptUnitTest.expectedOutputJson.value}
                  onChange={handleEditorScriptTestUnitOutputChange}
                />
              </div>
            </Stack>
          </Stack>
        </main>
      );
    }
    return null;
  };

  const scriptEditor = () => {
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
      >
        <Editor
          height={500}
          width="auto"
          options={generalEditorOptions()}
          defaultLanguage="python"
          value={scriptText}
          onChange={handleEditorScriptChange}
          onMount={handleEditorDidMount}
        />
        {scriptUnitTestEditorElement()}
      </Modal>
    );
  };
  const onLaunchMarkdownEditor = (
    element: any,
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
        size="xl"
        show={showMarkdownEditor}
        onHide={handleMarkdownEditorClose}
      >
        <Modal.Header closeButton>
          <Modal.Title>Edit Markdown Content</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <MDEditor value={markdownText} onChange={setMarkdownText} />
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleMarkdownEditorClose}>
            Close
          </Button>
        </Modal.Footer>
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
        if (file.references.some((ref) => ref.id === id)) {
          matchFile = file;
          return true;
        }
        return false;
      });
    }
    return matchFile;
  };

  /**
   * fixme:  Not currently in use.  This would only work for bpmn files within the process model.  Which is right for DMN and json, but not right here.  Need to merge in work on the nested process groups before tackling this.
   * @param processId
   */
  const onLaunchBpmnEditor = (processId: string) => {
    const file = findFileNameForReferenceId(processId, 'bpmn');
    if (file) {
      const path = generatePath(
        '/admin/process-models/:process_group_id/:process_model_id/files/:file_name',
        {
          process_group_id: params.process_group_id,
          process_model_id: params.process_model_id,
          file_name: file.name,
        }
      );
      window.open(path);
    }
  };
  const onLaunchJsonEditor = (fileName: string) => {
    const path = generatePath(
      '/admin/process-models/:process_group_id/:process_model_id/form/:file_name',
      {
        process_group_id: params.process_group_id,
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
        '/admin/process-models/:process_group_id/:process_model_id/files/:file_name',
        {
          process_group_id: params.process_group_id,
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
      />
    );
  };

  // if a file name is not given then this is a new model and the ReactDiagramEditor component will handle it
  if ((bpmnXmlForDiagramRendering || !params.file_name) && processModel) {
    return (
      <>
        <ProcessBreadcrumb
          processGroupId={params.process_group_id}
          processModelId={params.process_model_id}
          linkProcessModel
        />
        <h2>
          Process Model File
          {processModelFile ? `: ${(processModelFile as any).name}` : ''}
        </h2>
        {appropriateEditor()}
        {newFileNameBox()}
        {scriptEditor()}
        {markdownEditor()}

        <div id="diagram-container" />
      </>
    );
  }
  return null;
}
