import { useEffect, useState } from 'react';
import { JsonSchemaEditorState, MarkdownEditorState } from './useBpmnEditorLaunchers';

export interface UseBpmnEditorTextEditorsStateOptions {
  markdownEditorState?: MarkdownEditorState | null;
  jsonSchemaEditorState?: JsonSchemaEditorState | null;
}

export interface BpmnEditorTextEditorsState {
  markdownText: string;
  setMarkdownText: (value: string) => void;
  markdownEventBus: any;
  jsonSchemaFileName: string;
  setJsonSchemaFileName: (value: string) => void;
  fileEventBus: any;
}

export function useBpmnEditorTextEditorsState(
  options: UseBpmnEditorTextEditorsStateOptions
): BpmnEditorTextEditorsState {
  const { markdownEditorState, jsonSchemaEditorState } = options;
  const [markdownText, setMarkdownText] = useState<string>('');
  const [markdownEventBus, setMarkdownEventBus] = useState<any>(null);
  const [jsonSchemaFileName, setJsonSchemaFileName] = useState<string>('');
  const [fileEventBus, setFileEventBus] = useState<any>(null);

  useEffect(() => {
    if (!markdownEditorState) {
      return;
    }
    setMarkdownText(markdownEditorState.markdown || '');
    setMarkdownEventBus(markdownEditorState.eventBus);
  }, [markdownEditorState]);

  useEffect(() => {
    if (!jsonSchemaEditorState) {
      return;
    }
    setFileEventBus(jsonSchemaEditorState.eventBus);
    setJsonSchemaFileName(jsonSchemaEditorState.fileName);
  }, [jsonSchemaEditorState]);

  return {
    markdownText,
    setMarkdownText,
    markdownEventBus,
    jsonSchemaFileName,
    setJsonSchemaFileName,
    fileEventBus,
  };
}
