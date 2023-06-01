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
}

export default function TypeaheadWidget({
  id,
  onChange,
  options: { category, itemFormat },
  value,
  uiSchema,
  disabled,
  readonly,
  rawErrors = [],
}: typeaheadArgs) {
  const lastSearchTerm = useRef('');
  const [items, setItems] = useState<any[]>([]);
  const [selectedItem, setSelectedItem] = useState<any>(null);
  const itemFormatRegex = /[^{}]+(?=})/g;
  const itemFormatSubstitutions = itemFormat.match(itemFormatRegex);

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
    itemFormatSubstitutions.forEach((key: string) => {
      str = str.replace(`{${key}}`, item[key]);
    });
    return str;
  };

  let helperText = null;
  if (uiSchema && uiSchema['ui:help']) {
    helperText = uiSchema['ui:help'];
  }

  let invalid = false;
  let errorMessageForField = null;
  if (rawErrors && rawErrors.length > 0) {
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
      placeholder={`Start typing to search for ${category}...`}
      selectedItem={selectedItem}
      helperText={helperText}
      disabled={disabled}
      readOnly={readonly}
      invalid={invalid}
      invalidText={errorMessageForField}
    />
  );
}
