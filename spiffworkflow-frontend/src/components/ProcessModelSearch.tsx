import React from 'react';
import { useTranslation } from 'react-i18next';
import Autocomplete from '@mui/material/Autocomplete';
import TextField from '@mui/material/TextField';
import { ProcessGroupLite, ProcessModel } from '../interfaces';

type OwnProps = {
  onChange: (..._args: any[]) => any;
  processModels: ProcessModel[];
  selectedItem?: ProcessModel | null;
  titleText?: string;
  truncateProcessModelDisplayName?: boolean;
};

export default function ProcessModelSearch({
  processModels,
  selectedItem,
  onChange,
  titleText = undefined,
  truncateProcessModelDisplayName = false,
}: OwnProps) {
  const getParentGroupsDisplayName = (processModel: ProcessModel) => {
    if (processModel.parent_groups) {
      return processModel.parent_groups
        .map((parentGroup: ProcessGroupLite) => {
          return parentGroup.display_name;
        })
        .join(' / ');
    }
    return '';
  };

  const getProcessModelLabelForDisplay = (processModel: ProcessModel) => {
    let processModelId = processModel.id;
    if (truncateProcessModelDisplayName) {
      let processModelIdArray = processModelId.split('/');
      if (processModelIdArray.length > 2) {
        processModelIdArray = processModelIdArray.slice(-2);
        processModelIdArray.unshift('...');
      }
      processModelId = processModelIdArray.join('/');
    }
    return `${processModel.display_name} - ${processModelId}`;
  };

  const getProcessModelLabelForSearch = (processModel: ProcessModel) => {
    return `${processModel.display_name} ${
      processModel.id
    } ${getParentGroupsDisplayName(processModel)}`;
  };

  const shouldFilterProcessModel = (options: any) => {
    const processModel: ProcessModel = options.item;
    let { inputValue } = options;
    if (!inputValue) {
      inputValue = '';
    }
    const inputValueArray = inputValue.split(' ');
    const processModelLowerCase =
      getProcessModelLabelForSearch(processModel).toLowerCase();

    return inputValueArray.every((i: any) => {
      return processModelLowerCase.includes((i || '').toLowerCase());
    });
  };

  const { t } = useTranslation();
  return (
    <Autocomplete
      onChange={(_, value) => onChange(value)}
      id="process-model-select"
      data-testid="process-model-selection"
      options={processModels}
      getOptionLabel={(processModel: ProcessModel) => {
        if (processModel) {
          return getProcessModelLabelForDisplay(processModel);
        }
        return '';
      }}
      filterOptions={(options, state) =>
        options.filter((option) =>
          shouldFilterProcessModel({
            item: option,
            inputValue: state.inputValue,
          }),
        )
      }
      renderInput={(params) => (
        <TextField
          {...params}
          label={titleText || t('process_model')}
          placeholder={t('choose_process_model')}
        />
      )}
      value={selectedItem || null}
      className="process-model-search-combobox"
    />
  );
}
