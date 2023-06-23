import { ComboBox } from '@carbon/react';
import { useRef, useState } from 'react';
import { useDebouncedCallback } from 'use-debounce';
import { User } from '../interfaces';
import HttpService from '../services/HttpService';

type OwnProps = {
  onSelectedUser: Function;
};

export default function UserSearch({ onSelectedUser }: OwnProps) {
  const lastRequestedInitatorSearchTerm = useRef<string>();
  const [selectedUser, setSelectedUser] = useState<string | null>(null);
  const [userList, setUserList] = useState<string[]>([]);

  const handleUserSearchResult = (result: any, inputText: string) => {
    if (lastRequestedInitatorSearchTerm.current === result.username_prefix) {
      setUserList(result.users.map((user: User) => user.username));
      result.users.forEach((user: User) => {
        if (user.username === inputText) {
          setSelectedUser(user.username);
        }
      });
    }
  };

  const searchForUser = (inputText: string) => {
    if (inputText) {
      lastRequestedInitatorSearchTerm.current = inputText;
      HttpService.makeCallToBackend({
        path: `/users/search?username_prefix=${inputText}`,
        successCallback: (result: any) =>
          handleUserSearchResult(result, inputText),
      });
    }
  };

  const addDebouncedSearchUser = useDebouncedCallback(
    (value: string) => {
      searchForUser(value);
    },
    // delay in ms
    250
  );
  return (
    <ComboBox
      onInputChange={addDebouncedSearchUser}
      className="user-search-class"
      onChange={onSelectedUser}
      id="user-search"
      data-qa="user-search"
      items={userList}
      itemToString={(processInstanceInitatorOption: User) => {
        if (processInstanceInitatorOption) {
          return processInstanceInitatorOption;
        }
        return null;
      }}
      placeholder="Start typing username"
      titleText="Started by"
      selectedItem={selectedUser}
    />
  );
}
