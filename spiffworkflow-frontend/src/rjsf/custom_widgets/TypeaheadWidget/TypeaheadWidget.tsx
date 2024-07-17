import { useCallback, useEffect, useRef, useState } from 'react';
import { ComboBox } from '@carbon/react';
import HttpService from '../../../services/HttpService';
import { getCommonAttributes } from '../../helpers';

interface typeaheadArgs {
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

// eslint-disable-next-line sonarjs/cognitive-complexity
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
}: typeaheadArgs) {
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
    <ComboBox
      onInputChange={typeaheadSearch}
      onChange={(event: any) => {
        setSelectedItem(event.selectedItem);
        let valueToUse = event.selectedItem;

        // if the value is not truthy then do not stringify it
        // otherwise things like null becomes "null"
        if (valueToUse) {
          valueToUse = JSON.stringify(valueToUse);
        }

        onChange(valueToUse);
      }}
      id={id}
      items={items}
      itemToString={itemToString}
      placeholder={placeholderText}
      selectedItem={selectedItem}
      helperText={
        reactJsonSchemaFormTheme === 'mui' ? '' : commonAttributes.helperText
      }
      disabled={disabled}
      readOnly={readonly}
      invalid={commonAttributes.invalid}
      invalidText={commonAttributes.errorMessageForField}
    />
  );
}
