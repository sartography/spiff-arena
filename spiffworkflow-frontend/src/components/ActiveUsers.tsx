import { useEffect, useState } from 'react';

import HttpService from '../services/HttpService';
import {
  encodeBase64,
  refreshAtInterval,
  REFRESH_TIMEOUT_SECONDS,
} from '../helpers';
import { User } from '../interfaces';

export default function ActiveUsers() {
  // Handles getting and displaying active users.
  const [activeUsers, setActiveUsers] = useState<User[]>([]);

  const lastVisitedIdentifier = encodeBase64(window.location.pathname);
  useEffect(() => {
    const updateActiveUsers = () => {
      HttpService.makeCallToBackend({
        path: `/active-users/updates/${lastVisitedIdentifier}`,
        successCallback: setActiveUsers,
        httpMethod: 'POST',
      });
    };

    const unregisterUser = () => {
      HttpService.makeCallToBackend({
        path: `/active-users/unregister/${lastVisitedIdentifier}`,
        successCallback: setActiveUsers,
        httpMethod: 'POST',
      });
    };
    updateActiveUsers();

    return refreshAtInterval(
      15,
      REFRESH_TIMEOUT_SECONDS,
      updateActiveUsers,
      unregisterUser
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // it is critical to only run this once.

  // activeUsers is supposed to be an array, but it is based on the response body
  // from a network call, so who knows what might happen. Be safe.
  if (!activeUsers.map) {
    return null;
  }

  const au = activeUsers.map((activeUser: User) => {
    return (
      <div
        title={`${activeUser.username} is also viewing this page`}
        className="user-circle user-circle-for-list"
      >
        {activeUser.username.charAt(0).toUpperCase()}
      </div>
    );
  });
  return <div className="user-list">{au}</div>;
}
