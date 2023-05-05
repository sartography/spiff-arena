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
      });
    };

    const unregisterUser = () => {
      HttpService.makeCallToBackend({
        path: `/active-users/unregister/${lastVisitedIdentifier}`,
        successCallback: setActiveUsers,
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

  const au = activeUsers.map((activeUser: User) => {
    return (
      <div
        title={`${activeUser.username} is also viewing this page`}
        className="user-circle"
      >
        {activeUser.username.charAt(0).toUpperCase()}
      </div>
    );
  });
  return <div className="user-list">{au}</div>;
}
