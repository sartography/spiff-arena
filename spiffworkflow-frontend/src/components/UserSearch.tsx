import { ComboBox } from '@carbon/react';
import { useRef, useState } from 'react';
import { useDebouncedCallback } from 'use-debounce';
import { CarbonComboBoxSelection, User } from '../interfaces';
import HttpService from '../services/HttpService';

type OwnProps = {
  onSelectedUser: Function;
  label?: string;
  className?: string;
};

export default function UserSearch({
  onSelectedUser,
  className,
  label = 'User',
}: OwnProps) {
  const lastRequestedInitatorSearchTerm = useRef<string>();
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [userList, setUserList] = useState<User[]>([]);

  const handleUserSearchResult = (result: any, inputText: string) => {
    if (lastRequestedInitatorSearchTerm.current === result.username_prefix) {
      setUserList(result.users);
      result.users.forEach((user: User) => {
        if (user.username === inputText) {
          setSelectedUser(user);
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
    250,
  );
  return (
    <ComboBox
      onInputChange={addDebouncedSearchUser}
      className={className}
      onChange={(selection: CarbonComboBoxSelection) => {
        onSelectedUser(selection.selectedItem);
      }}
      id="user-search"
      data-qa="user-search"
      items={userList}
      itemToString={(processInstanceInitatorOption: User) => {
        if (processInstanceInitatorOption) {
          return processInstanceInitatorOption.username;
        }
        return null;
      }}
      placeholder="Start typing username"
      titleText={label}
      selectedItem={selectedUser}
    />
  );
}
