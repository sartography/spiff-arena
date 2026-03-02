import React, { useState, useRef, SyntheticEvent } from 'react';
import { Dialog, Box, Button, Tabs, Tab } from '@mui/material';
import { Editor } from '@monaco-editor/react';

export interface ScriptEditorModalProps {
  isOpen: boolean;
  script: string;
  scriptType: string;
  scriptName?: string;
  onClose: () => void;
  onScriptChange: (script: string) => void;
}

function TabPanel(props: {
  children?: React.ReactNode;
  index: number;
  value: number;
}) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`script-tabpanel-${index}`}
      aria-labelledby={`script-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export function ScriptEditorModal({
  isOpen,
  script,
  scriptType,
  scriptName = 'Script',
  onClose,
  onScriptChange,
}: ScriptEditorModalProps) {
  const [tabValue, setTabValue] = useState<number>(0);
  const editorRef = useRef(null);
  const monacoRef = useRef(null);

  const handleTabChange = (_event: SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  function handleEditorDidMount(editor: any, monaco: any) {
    editorRef.current = editor;
    monacoRef.current = monaco;
  }

  const generalEditorOptions = () => {
    return {
      glyphMargin: false,
      folding: false,
      lineNumbersMinChars: 0,
    };
  };

  if (!isOpen) {
    return null;
  }

  return (
    <Dialog
      className="bpmn-editor-wide-dialog"
      open={isOpen}
      onClose={onClose}
      aria-labelledby="script-editor-title"
      maxWidth="lg"
      fullWidth
    >
      <Box sx={{ p: 4 }}>
        <h2 id="script-editor-title">
          Edit Script: {scriptName}
        </h2>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="Script Editor" />
          <Tab label="Unit Tests" />
        </Tabs>
        <Box>
          <TabPanel value={tabValue} index={0}>
            <Editor
              height={500}
              width="auto"
              options={generalEditorOptions()}
              defaultLanguage="python"
              defaultValue={script}
              value={script}
              onChange={(value) => onScriptChange(value || '')}
              onMount={handleEditorDidMount}
            />
          </TabPanel>
          <TabPanel value={tabValue} index={1}>
            <p>Unit tests editor not yet implemented in package. Override this component to add unit test functionality.</p>
          </TabPanel>
        </Box>
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
          <Button onClick={onClose} variant="contained">Close</Button>
        </Box>
      </Box>
    </Dialog>
  );
}

export default ScriptEditorModal;
