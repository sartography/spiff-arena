import { useCallback, useEffect, useRef, useState } from 'react';
import { ComboBox } from '@carbon/react';
import HttpService from '../../../services/HttpService';

interface typeaheadArgs {
  id: string;
  onChange: any;
  options: any;
  value: any;
  uiSchema?: any;
  disabled?: boolean;
  readonly?: boolean;
  rawErrors?: any;
  placeholder?: string;
  label?: string;
}

export default function TypeaheadWidget({
  id,
  onChange,
  options: { category, itemFormat },
  value,
  uiSchema,
  disabled,
  readonly,
  placeholder,
  label,
  rawErrors = [],
}: typeaheadArgs) {
  const lastSearchTerm = useRef('');
  const [items, setItems] = useState<any[]>([]);
  const [selectedItem, setSelectedItem] = useState<any>(null);
  const itemFormatRegex = /[^{}]+(?=})/g;

  let itemFormatSubstitutions: string[] | null = null;
  let invalid = false;
  let errorMessageForField = null;

  if (itemFormat) {
    try {
      itemFormatSubstitutions = itemFormat.match(itemFormatRegex);
    } catch (e) {
      errorMessageForField = `itemFormat does not contain replacement keys in curly braces. It should be like: "{key1} ({key2} - {key3})"`;
      invalid = true;
    }
  }

  if (!category) {
    errorMessageForField = `category is not set in the ui:options for this field: ${label}`;
    invalid = true;
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
    [category]
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

  let helperText = null;
  if (uiSchema && uiSchema['ui:help']) {
    helperText = uiSchema['ui:help'];
  }

  if (!invalid && rawErrors && rawErrors.length > 0) {
    invalid = true;
    [errorMessageForField] = rawErrors;
  }

  return (
    <ComboBox
      onInputChange={typeaheadSearch}
      onChange={(event: any) => {
        setSelectedItem(event.selectedItem);
        onChange(JSON.stringify(event.selectedItem));
      }}
      id={id}
      items={items}
      itemToString={itemToString}
      placeholder={placeholderText}
      selectedItem={selectedItem}
      helperText={helperText}
      disabled={disabled}
      readOnly={readonly}
      invalid={invalid}
      invalidText={errorMessageForField}
    />
  );
}
