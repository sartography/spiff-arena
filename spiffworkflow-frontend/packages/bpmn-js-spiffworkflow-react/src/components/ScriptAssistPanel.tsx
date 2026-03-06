import React from 'react';
import { Button, CircularProgress, Stack, TextareaAutosize } from '@mui/material';

type ScriptAssistPanelProps = {
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  error?: string | null;
  loading?: boolean;
  buttonLabel: string;
  onSubmit: () => void;
  minRows?: number;
};

export default function ScriptAssistPanel({
  value,
  onChange,
  placeholder,
  error,
  loading = false,
  buttonLabel,
  onSubmit,
  minRows = 20,
}: ScriptAssistPanelProps) {
  return (
    <>
      <TextareaAutosize
        placeholder={placeholder}
        minRows={minRows}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        style={{ width: '100%' }}
        aria-label={placeholder}
      />
      <Stack direction="row" justifyContent="flex-end" alignItems="center" spacing={2}>
        {error ? <div style={{ color: 'red' }}>{error}</div> : null}
        {loading ? <CircularProgress /> : null}
        <Button variant="contained" onClick={onSubmit} disabled={loading}>
          {buttonLabel}
        </Button>
      </Stack>
    </>
  );
}
