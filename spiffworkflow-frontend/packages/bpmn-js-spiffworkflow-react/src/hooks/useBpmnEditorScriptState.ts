import { useEffect, useState } from 'react';
import { ScriptEditorState } from './useBpmnEditorLaunchers';

export interface UseBpmnEditorScriptStateOptions {
  scriptEditorState?: ScriptEditorState | null;
}

export interface BpmnEditorScriptState {
  scriptText: string;
  setScriptText: (value: string) => void;
  scriptType: string;
  scriptEventBus: any;
  scriptElement: any;
  scriptModeling: any;
}

export function useBpmnEditorScriptState(
  options: UseBpmnEditorScriptStateOptions
): BpmnEditorScriptState {
  const { scriptEditorState } = options;
  const [scriptText, setScriptText] = useState<string>('');
  const [scriptType, setScriptType] = useState<string>('');
  const [scriptEventBus, setScriptEventBus] = useState<any>(null);
  const [scriptElement, setScriptElement] = useState<any>(null);
  const [scriptModeling, setScriptModeling] = useState<any>(null);

  useEffect(() => {
    if (!scriptEditorState) {
      return;
    }
    setScriptModeling(scriptEditorState.modeling);
    setScriptText(scriptEditorState.script || '');
    setScriptType(scriptEditorState.scriptType);
    setScriptEventBus(scriptEditorState.eventBus);
    setScriptElement(scriptEditorState.element);
  }, [scriptEditorState]);

  return {
    scriptText,
    setScriptText,
    scriptType,
    scriptEventBus,
    scriptElement,
    scriptModeling,
  };
}
