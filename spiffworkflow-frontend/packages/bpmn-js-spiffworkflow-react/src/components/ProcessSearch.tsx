import React from 'react';
import { Autocomplete, TextField } from '@mui/material';
import { ProcessReference } from '../hooks/useProcessReferences';

type ProcessSearchProps = {
  onChange: (..._args: any[]) => any;
  processes: ProcessReference[];
  selectedItem?: ProcessReference | null;
  titleText?: string;
  placeholderText?: string;
  height?: string;
};

const truncateString = (value: string, maxLength: number) => {
  if (value.length <= maxLength) {
    return value;
  }
  return `${value.slice(0, maxLength - 3)}...`;
};

export default function ProcessSearch({
  processes,
  selectedItem,
  onChange,
  titleText,
  placeholderText,
  height = '50px',
}: ProcessSearchProps) {
  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Escape') {
      onChange(null);
    }
  };

  const shouldFilter = (options: any) => {
    const { process, inputValue } = options;
    return (
      inputValue === null ||
      `${process.display_name} (${process.identifier})`
        .toLowerCase()
        .includes(inputValue.toLowerCase())
    );
  };

  if (processes) {
    return (
      <div style={{ width: '100%', height }}>
        <Autocomplete
          id="process-model-select"
          data-testid="process-model-selection"
          options={processes}
          disablePortal
          value={selectedItem || null}
          onChange={(_, value) => onChange(value)}
          renderInput={(params) => {
            return (
              <TextField
                label={titleText || 'Process Search'}
                placeholder={placeholderText || 'Choose a process'}
                variant="outlined"
                onKeyDown={handleKeyDown}
                {...params}
                InputLabelProps={{ shrink: true }}
              />
            );
          }}
          getOptionLabel={(process: ProcessReference) => {
            if (process) {
              return `${process.display_name} (${truncateString(
                process.identifier,
                75,
              )})`;
            }
            return '';
          }}
          filterOptions={(options, state) => {
            const result = options.filter((option) =>
              shouldFilter({ process: option, inputValue: state.inputValue }),
            );
            return result;
          }}
        />
      </div>
    );
  }
  return null;
}
