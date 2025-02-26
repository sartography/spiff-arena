import React from 'react';
import { Autocomplete, TextField } from '@mui/material';
import { ProcessReference } from '../interfaces';
import { truncateString } from '../helpers';

type OwnProps = {
  onChange: (..._args: any[]) => any;
  processes: ProcessReference[];
  selectedItem?: ProcessReference | null;
  titleText?: string;
  height?: string;
};

export default function ProcessSearch({
  processes,
  selectedItem,
  onChange,
  titleText = 'Process Search',
  height = '50px',
}: OwnProps) {
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
          data-qa="process-model-selection"
          options={processes}
          disablePortal
          value={selectedItem || null}
          onChange={(_, value) => onChange(value)}
          renderInput={(params) => {
            return (
              <TextField
                label={titleText}
                placeholder="Choose a process"
                variant="outlined"
                fullWidth
                slotProps={{
                  input: params.InputProps,
                  htmlInput: params.inputProps,
                  inputLabel: { shrink: true },
                }}
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
