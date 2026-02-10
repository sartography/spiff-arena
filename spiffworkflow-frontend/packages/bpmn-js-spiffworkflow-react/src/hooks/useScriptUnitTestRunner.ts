export interface ScriptUnitTestRunPayload {
  bpmn_task_identifier: string;
  python_script: string;
  input_json: any;
  expected_output_json: any;
}

export interface RunScriptUnitTestOptions {
  currentScriptUnitTest: any;
  scriptElement: any;
  scriptText: string;
  onResult: (result: any) => void;
  onInvalidJson: () => void;
  beforeRun?: () => void;
  runRequest: (payload: ScriptUnitTestRunPayload) => Promise<any>;
}

export async function runScriptUnitTest(
  options: RunScriptUnitTestOptions,
): Promise<void> {
  const {
    currentScriptUnitTest,
    scriptElement,
    scriptText,
    onResult,
    onInvalidJson,
    beforeRun,
    runRequest,
  } = options;

  if (!currentScriptUnitTest || !scriptElement) {
    return;
  }

  let inputJson = '';
  let expectedJson = '';
  try {
    inputJson = JSON.parse(currentScriptUnitTest.inputJson.value);
    expectedJson = JSON.parse(currentScriptUnitTest.expectedOutputJson.value);
  } catch (_) {
    onInvalidJson();
    return;
  }

  if (beforeRun) {
    beforeRun();
  }

  const payload: ScriptUnitTestRunPayload = {
    bpmn_task_identifier: scriptElement.id,
    python_script: scriptText,
    input_json: inputJson,
    expected_output_json: expectedJson,
  };

  const result = await runRequest(payload);
  onResult(result);
}
