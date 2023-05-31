import { useRef, useState } from 'react';
import { ComboBox } from '@carbon/react';
import HttpService from '../../../services/HttpService';

export default function TypeaheadWidget({
  id,
  onChange,
  options: { category, itemFormat },
}: {
  id: string;
  onChange: any;
  options: any;
}) {
  const pathForCategory = (inputText: string) => {
    return `/connector-proxy/typeahead/${category}?prefix=${inputText}&limit=100`;
  };

  const lastSearchTerm = useRef('');
  const [items, setItems] = useState<any[]>([]);
  const [selectedItem, setSelectedItem] = useState<any>(null);
  const itemFormatRegex = /[^{}]+(?=})/g;
  const itemFormatSubstitutions = itemFormat.match(itemFormatRegex);

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

  return (
    <ComboBox
      onInputChange={typeaheadSearch}
      onChange={(event: any) => {
        setSelectedItem(event.selectedItem);
        onChange(itemToString(event.selectedItem));
      }}
      id={id}
      items={items}
      itemToString={itemToString}
      placeholder={`Start typing to search for ${category}...`}
      selectedItem={selectedItem}
    />
  );
}
