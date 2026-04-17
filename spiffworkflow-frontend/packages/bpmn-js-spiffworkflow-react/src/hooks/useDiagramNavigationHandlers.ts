import { useCallback, useEffect, useRef } from 'react';
import type { DiagramNavigationItem } from './useDiagramNavigationStack';
import type { ProcessModel } from '../types';
import type { ProcessReference } from './useProcessReferences';
import { findFileNameForReferenceId } from './useBpmnEditorCallbacks';

type UseDiagramNavigationHandlersOptions = {
  processes: ProcessReference[];
  refreshProcesses: () => Promise<ProcessReference[]>;
  processModel?: ProcessModel | null;
  currentProcessModelId?: string;
  normalizeProcessModelId: (value: string) => string;
  pushNavigation: (item: DiagramNavigationItem) => void;
  navigateTo: (path: string) => void;
  buildProcessFilePath: (item: DiagramNavigationItem) => string;
  buildDmnListPath?: (processModelId: string) => string;
};

export function useDiagramNavigationHandlers({
  processes,
  refreshProcesses,
  processModel,
  currentProcessModelId,
  normalizeProcessModelId,
  pushNavigation,
  navigateTo,
  buildProcessFilePath,
  buildDmnListPath,
}: UseDiagramNavigationHandlersOptions) {
  const processesRef = useRef(processes);
  const refreshRef = useRef(refreshProcesses);
  const processModelRef = useRef(processModel);
  const currentProcessModelIdRef = useRef(currentProcessModelId);
  const normalizeRef = useRef(normalizeProcessModelId);
  const pushNavigationRef = useRef(pushNavigation);
  const navigateRef = useRef(navigateTo);
  const buildPathRef = useRef(buildProcessFilePath);
  const buildDmnListPathRef = useRef(buildDmnListPath);

  useEffect(() => {
    processesRef.current = processes;
  }, [processes]);
  useEffect(() => {
    refreshRef.current = refreshProcesses;
  }, [refreshProcesses]);
  useEffect(() => {
    processModelRef.current = processModel;
  }, [processModel]);
  useEffect(() => {
    currentProcessModelIdRef.current = currentProcessModelId;
  }, [currentProcessModelId]);
  useEffect(() => {
    normalizeRef.current = normalizeProcessModelId;
  }, [normalizeProcessModelId]);
  useEffect(() => {
    pushNavigationRef.current = pushNavigation;
  }, [pushNavigation]);
  useEffect(() => {
    navigateRef.current = navigateTo;
  }, [navigateTo]);
  useEffect(() => {
    buildPathRef.current = buildProcessFilePath;
  }, [buildProcessFilePath]);
  useEffect(() => {
    buildDmnListPathRef.current = buildDmnListPath;
  }, [buildDmnListPath]);

  const openProcessReference = useCallback(
    (processReference: ProcessReference, processId: string) => {
      const modifiedProcessModelId = normalizeRef.current(
        processReference.relative_location,
      );
      const item: DiagramNavigationItem = {
        modifiedProcessModelId,
        fileName: processReference.file_name,
        displayName: processReference.display_name || processId,
      };
      pushNavigationRef.current(item);
      navigateRef.current(buildPathRef.current(item));
    },
    [],
  );

  const onLaunchBpmnEditor = useCallback(
    (processId: string) => {
      const processRef = processesRef.current.find(
        (p) => p.identifier === processId,
      );
      if (processRef) {
        openProcessReference(processRef, processId);
        return;
      }

      refreshRef.current().then((freshProcesses) => {
        const nextRef = freshProcesses.find((p) => p.identifier === processId);
        if (nextRef) {
          openProcessReference(nextRef, processId);
        }
      });
    },
    [openProcessReference],
  );

  const onLaunchDmnEditor = useCallback(
    (processId: string) => {
      const file = findFileNameForReferenceId(
        processModelRef.current,
        processId,
        'dmn',
      );
      const currentId = currentProcessModelIdRef.current;
      if (file && currentId) {
        const item: DiagramNavigationItem = {
          modifiedProcessModelId: currentId,
          fileName: file.name,
          displayName: processId,
        };
        pushNavigationRef.current(item);
        navigateRef.current(buildPathRef.current(item));
        return;
      }
      if (buildDmnListPathRef.current && currentId) {
        navigateRef.current(buildDmnListPathRef.current(currentId));
      }
    },
    [],
  );

  return {
    onLaunchBpmnEditor,
    onLaunchDmnEditor,
  };
}
