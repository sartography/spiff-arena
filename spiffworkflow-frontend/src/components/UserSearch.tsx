import { Autocomplete, TextField } from '@mui/material';
import { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useDebouncedCallback } from 'use-debounce';
import { User } from '../interfaces';
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
  const { t } = useTranslation();
  const lastRequestedInitatorSearchTerm = useRef<string>();
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [userList, setUserList] = useState<User[]>([]);

  const handleUserSearchResult = (result: any, inputText: string) => {
    if (lastRequestedInitatorSearchTerm.current === result.username_prefix) {
      setUserList(result.users);
      result.users.forEach((user: User) => {
        if (user.username === inputText) {
          setSelectedUser(user);
          onSelectedUser(user);
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
    <Autocomplete
      onInputChange={(_event, value) => addDebouncedSearchUser(value)}
      className={className}
      onChange={(_event, value) => {
        onSelectedUser(value);
      }}
      id="user-search"
      data-testid="user-search"
      options={userList}
      getOptionLabel={(option: User) => option.username || ''}
      renderInput={(params) => (
        <TextField
          {...params}
          label={label}
          placeholder={t('enter_username')}
        />
      )}
      value={selectedUser}
    />
  );
}
