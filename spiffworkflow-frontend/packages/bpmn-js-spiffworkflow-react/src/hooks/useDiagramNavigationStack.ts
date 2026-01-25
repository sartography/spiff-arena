import { useCallback, useState } from 'react';

export type DiagramNavigationItem = {
  processModelId: string;
  fileName: string;
  displayName?: string;
};

type UseDiagramNavigationStackResult = {
  stack: DiagramNavigationItem[];
  push: (item: DiagramNavigationItem) => void;
  reset: (item: DiagramNavigationItem) => void;
  popToIndex: (index: number) => void;
  updateTop: (updates: Partial<DiagramNavigationItem>) => void;
};

export function useDiagramNavigationStack(
  initialItem?: DiagramNavigationItem,
): UseDiagramNavigationStackResult {
  const [stack, setStack] = useState<DiagramNavigationItem[]>(
    initialItem ? [initialItem] : [],
  );

  const push = useCallback((item: DiagramNavigationItem) => {
    setStack((prev) => [...prev, item]);
  }, []);

  const reset = useCallback((item: DiagramNavigationItem) => {
    setStack([item]);
  }, []);

  const popToIndex = useCallback((index: number) => {
    setStack((prev) => prev.slice(0, index + 1));
  }, []);

  const updateTop = useCallback((updates: Partial<DiagramNavigationItem>) => {
    setStack((prev) => {
      if (prev.length === 0) {
        return prev;
      }
      const next = [...prev];
      next[next.length - 1] = { ...next[next.length - 1], ...updates };
      return next;
    });
  }, []);

  return {
    stack,
    push,
    reset,
    popToIndex,
    updateTop,
  };
}
