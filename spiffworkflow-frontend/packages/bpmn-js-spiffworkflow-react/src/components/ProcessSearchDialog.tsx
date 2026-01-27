import React from 'react';
import DialogShell from './DialogShell';
import ProcessSearch from './ProcessSearch';
import type { ProcessReference } from '../hooks/useProcessReferences';

type ProcessSearchDialogProps = {
  open: boolean;
  title: string;
  processes: ProcessReference[];
  onChange: (selection: ProcessReference) => void;
  titleText: string;
  placeholderText: string;
  height?: string;
};

export default function ProcessSearchDialog({
  open,
  title,
  processes,
  onChange,
  titleText,
  placeholderText,
  height = '500px',
}: ProcessSearchDialogProps) {
  return (
    <DialogShell open={open} onClose={() => onChange(null as any)} title={title}>
      <ProcessSearch
        height={height}
        onChange={onChange}
        processes={processes}
        titleText={titleText}
        placeholderText={placeholderText}
      />
    </DialogShell>
  );
}
