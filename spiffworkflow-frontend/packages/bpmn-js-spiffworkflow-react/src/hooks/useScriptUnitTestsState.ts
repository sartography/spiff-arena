import { useCallback, useState } from 'react';

export interface ScriptUnitTestState {
  currentScriptUnitTest: any;
  currentScriptUnitTestIndex: number;
  scriptUnitTestResult: any;
}

export interface ScriptUnitTestActions {
  setScriptUnitTestElementWithIndex: (scriptIndex: number, element: any) => void;
  setPreviousScriptUnitTest: (element: any) => void;
  setNextScriptUnitTest: (element: any) => void;
  updateInputJson: (value: any, element: any, modeling: any) => void;
  updateExpectedOutputJson: (value: any, element: any, modeling: any) => void;
  setScriptUnitTestResult: (result: any) => void;
  resetScriptUnitTestResult: () => void;
  setCurrentScriptUnitTest: (test: any) => void;
  setCurrentScriptUnitTestIndex: (index: number) => void;
}

export interface UseScriptUnitTestsStateOptions {
  getScriptUnitTestElements: (element: any) => any[];
}

export function useScriptUnitTestsState(
  options: UseScriptUnitTestsStateOptions
): [ScriptUnitTestState, ScriptUnitTestActions] {
  const { getScriptUnitTestElements } = options;
  const [currentScriptUnitTest, setCurrentScriptUnitTest] = useState<any>(null);
  const [currentScriptUnitTestIndex, setCurrentScriptUnitTestIndex] =
    useState<number>(-1);
  const [scriptUnitTestResult, setScriptUnitTestResult] = useState<any>(null);

  const setScriptUnitTestElementWithIndex = useCallback(
    (scriptIndex: number, element: any) => {
      const unitTestsModdleElements = getScriptUnitTestElements(element);
      if (unitTestsModdleElements.length > 0) {
        setCurrentScriptUnitTest(unitTestsModdleElements[scriptIndex]);
        setCurrentScriptUnitTestIndex(scriptIndex);
      }
    },
    [getScriptUnitTestElements]
  );

  const resetScriptUnitTestResult = useCallback(() => {
    setScriptUnitTestResult(null);
  }, []);

  const setPreviousScriptUnitTest = useCallback(
    (element: any) => {
      resetScriptUnitTestResult();
      const newScriptIndex = currentScriptUnitTestIndex - 1;
      if (newScriptIndex >= 0) {
        setScriptUnitTestElementWithIndex(newScriptIndex, element);
      }
    },
    [
      currentScriptUnitTestIndex,
      resetScriptUnitTestResult,
      setScriptUnitTestElementWithIndex,
    ]
  );

  const setNextScriptUnitTest = useCallback(
    (element: any) => {
      resetScriptUnitTestResult();
      const newScriptIndex = currentScriptUnitTestIndex + 1;
      const unitTestsModdleElements = getScriptUnitTestElements(element);
      if (newScriptIndex < unitTestsModdleElements.length) {
        setScriptUnitTestElementWithIndex(newScriptIndex, element);
      }
    },
    [
      currentScriptUnitTestIndex,
      getScriptUnitTestElements,
      resetScriptUnitTestResult,
      setScriptUnitTestElementWithIndex,
    ]
  );

  const updateInputJson = useCallback(
    (value: any, element: any, modeling: any) => {
      if (currentScriptUnitTest) {
        currentScriptUnitTest.inputJson.value = value;
        modeling?.updateProperties(element, {});
      }
    },
    [currentScriptUnitTest]
  );

  const updateExpectedOutputJson = useCallback(
    (value: any, element: any, modeling: any) => {
      if (currentScriptUnitTest) {
        currentScriptUnitTest.expectedOutputJson.value = value;
        modeling?.updateProperties(element, {});
      }
    },
    [currentScriptUnitTest]
  );

  return [
    {
      currentScriptUnitTest,
      currentScriptUnitTestIndex,
      scriptUnitTestResult,
    },
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
  ];
}
