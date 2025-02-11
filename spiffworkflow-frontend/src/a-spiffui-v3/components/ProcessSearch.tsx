import React from 'react';
import { Autocomplete, TextField } from '@mui/material';
import { truncateString } from '../helpers';
import { ProcessReference } from '../interfaces';

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
    const process: ProcessReference = options.item;
    const { inputValue } = options;
    return (
      inputValue === null ||
      `${process.display_name} (${process.identifier})`
        .toLowerCase()
        .includes(inputValue.toLowerCase())
    );
  };

  return (
    <div style={{ width: '100%', height }}>
      <Autocomplete
        onChange={(_, value) => onChange(value)}
        id="process-model-select"
        data-qa="process-model-selection"
        options={processes}
        getOptionLabel={(process: ProcessReference) => {
          if (process) {
            return `${process.display_name} (${truncateString(
              process.identifier,
              75,
            )})`;
          }
          return '';
        }}
        filterOptions={(options, state) =>
          options.filter((option) =>
            shouldFilter({ item: option, inputValue: state.inputValue }),
          )
        }
        renderInput={(params) => (
          <TextField
            {...params}
            label={titleText}
            placeholder="Choose a process"
          />
        )}
        value={selectedItem || null}
      />
    </div>
  );
}
