import { useCallback, useEffect, useRef, useState } from 'react';
import { Autocomplete, TextField } from '@mui/material';
import HttpService from '../../../services/HttpService';
import { getCommonAttributes } from '../../helpers';

interface TypeaheadArgs {
  id: string;
  onChange: any;
  options: any;
  value: any;
  label: string;
  schema?: any;
  uiSchema?: any;
  disabled?: boolean;
  readonly?: boolean;
  rawErrors?: any;
  placeholder?: string;
  reactJsonSchemaFormTheme?: string;
}

export default function TypeaheadWidget({
  id,
  onChange,
  options: { category, itemFormat },
  value,
  schema,
  uiSchema,
  disabled,
  readonly,
  placeholder,
  label,
  rawErrors = [],
  reactJsonSchemaFormTheme,
}: TypeaheadArgs) {
  const lastSearchTerm = useRef('');
  const [items, setItems] = useState<any[]>([]);
  const [selectedItem, setSelectedItem] = useState<any>(null);
  const itemFormatRegex = /[^{}]+(?=})/g;

  let itemFormatSubstitutions: string[] | null = null;

  const commonAttributes = getCommonAttributes(
    label,
    schema,
    uiSchema,
    rawErrors,
  );

  if (itemFormat) {
    try {
      itemFormatSubstitutions = itemFormat.match(itemFormatRegex);
    } catch (e) {
      commonAttributes.errorMessageForField = `itemFormat does not contain replacement keys in curly braces. It should be like: "{key1} ({key2} - {key3})"`;
      commonAttributes.invalid = true;
    }
  }

  const typeaheadSearch = useCallback(
    (inputText: string) => {
      const pathForCategory = (text: string) => {
        return `/connector-proxy/typeahead/${category}?prefix=${text}&limit=100`;
      };
      if (inputText) {
        lastSearchTerm.current = inputText;
        // TODO: check cache of prefixes -> results
        HttpService.makeCallToBackend({
          path: pathForCategory(inputText),
          successCallback: (result: any) => {
            if (lastSearchTerm.current === inputText) {
              setItems(result);
            }
          },
        });
      }
    },
    [category],
  );

  useEffect(() => {
    if (value) {
      setSelectedItem(JSON.parse(value));
      typeaheadSearch(value);
    }
  }, [value, typeaheadSearch]);

  const itemToString = (item: any) => {
    if (!item) {
      return null;
    }

    let str = itemFormat;
    if (itemFormatSubstitutions) {
      itemFormatSubstitutions.forEach((key: string) => {
        str = str.replace(`{${key}}`, item[key]);
      });
    } else {
      str = JSON.stringify(item);
    }
    return str;
  };

  let placeholderText = `Start typing to search...`;
  if (placeholder) {
    placeholderText = placeholder;
  }

  if (!category) {
    commonAttributes.errorMessageForField = `category is not set in the ui:options for this field: ${commonAttributes.label}`;
    commonAttributes.invalid = true;
  }

  return (
    <Autocomplete
      onInputChange={(_event, inputValue) => typeaheadSearch(inputValue)}
      onChange={(_event, nextSelectedItem) => {
        setSelectedItem(nextSelectedItem);
        let valueToUse = nextSelectedItem;

        // if the value is not truthy then do not stringify it
        // otherwise things like null becomes "null"
        if (valueToUse) {
          valueToUse = JSON.stringify(valueToUse);
        }

        onChange(valueToUse);
      }}
      id={id}
      options={items}
      getOptionLabel={(item) => itemToString(item) || ''}
      isOptionEqualToValue={(option, selectedValue) =>
        JSON.stringify(option) === JSON.stringify(selectedValue)
      }
      value={selectedItem}
      disabled={disabled}
      readOnly={readonly}
      renderInput={(params) => (
        <TextField
          {...params}
          label={commonAttributes.label}
          placeholder={placeholderText}
          error={commonAttributes.invalid}
          helperText={
            commonAttributes.invalid
              ? commonAttributes.errorMessageForField
              : reactJsonSchemaFormTheme === 'mui'
                ? ''
                : commonAttributes.helperText
          }
        />
      )}
    />
  );
}
