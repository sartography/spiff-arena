import { useEffect, useRef, useState } from 'react';
import { ComboBox } from '@carbon/react';
import HttpService from '../../../services/HttpService';

interface typeaheadArgs {
  id: string;
  onChange: any;
  options: any;
  value: any;
}

export default function TypeaheadWidget({
  id,
  onChange,
  options: { category, itemFormat },
  value,
  ...args
}: typeaheadArgs) {
  const pathForCategory = (inputText: string) => {
    return `/connector-proxy/typeahead/${category}?prefix=${inputText}&limit=100`;
  };
  console.log('args', args);
  console.log('value', value);
  console.log('itemFormat', itemFormat);

  // if (value) {
  //
  // }

  const lastSearchTerm = useRef('');
  const [items, setItems] = useState<any[]>([]);
  const [selectedItem, setSelectedItem] = useState<any>(null);
  const itemFormatRegex = /[^{}]+(?=})/g;
  const itemFormatSubstitutions = itemFormat.match(itemFormatRegex);

  useEffect(() => {
    if (value) {
      setSelectedItem(JSON.parse(value));
    }
    typeaheadSearch(value);
  }, [value]);

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

  const handleTypeAheadResult = (result: any, inputText: string) => {
    if (lastSearchTerm.current === inputText) {
      setItems(result);
    }
  };

  const typeaheadSearch = (inputText: string) => {
    if (inputText) {
      lastSearchTerm.current = inputText;
      // TODO: check cache of prefixes -> results
      HttpService.makeCallToBackend({
        path: pathForCategory(inputText),
        successCallback: (result: any) =>
          handleTypeAheadResult(result, inputText),
      });
    }
  };

  console.log('selectedItem', selectedItem);

  return (
    <ComboBox
      onInputChange={typeaheadSearch}
      onChange={(event: any) => {
        console.log('event.selectedItem', event.selectedItem);
        setSelectedItem(event.selectedItem);
        // onChange(itemToString(event.selectedItem));
        onChange(JSON.stringify(event.selectedItem));
      }}
      id={id}
      items={items}
      itemToString={itemToString}
      placeholder={`Start typing to search for ${category}...`}
      selectedItem={selectedItem}
    />
  );
}
