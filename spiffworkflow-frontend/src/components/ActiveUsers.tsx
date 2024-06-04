import { useEffect, useState } from 'react';

import HttpService from '../services/HttpService';
import { User } from '../interfaces';
import { refreshAtInterval } from '../helpers';
import DateAndTimeService from '../services/DateAndTimeService';

async function sha256(message: string) {
  // encode as UTF-8
  const msgBuffer = new TextEncoder().encode(message);

  // hash the message
  const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);

  // convert ArrayBuffer to Array
  const hashArray = Array.from(new Uint8Array(hashBuffer));

  // convert bytes to hex string
  return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
}

export default function ActiveUsers() {
  // Handles getting and displaying active users.
  const [activeUsers, setActiveUsers] = useState<User[]>([]);

  useEffect(() => {
    const updateActiveUsers = () => {
      const makeCall = (lastVisitedIdentifier: any) => {
        HttpService.makeCallToBackend({
          path: `/active-users/updates/${lastVisitedIdentifier}`,
          successCallback: setActiveUsers,
          httpMethod: 'POST',
        });
      };
      sha256(window.location.pathname).then(makeCall);
    };
    updateActiveUsers();

    const unregisterUser = () => {
      const makeCall = (lastVisitedIdentifier: any) => {
        HttpService.makeCallToBackend({
          path: `/active-users/unregister/${lastVisitedIdentifier}`,
          successCallback: setActiveUsers,
          httpMethod: 'POST',
        });
      };
      sha256(window.location.pathname).then(makeCall);
    };

    return refreshAtInterval(
      15,
      DateAndTimeService.REFRESH_TIMEOUT_SECONDS,
      updateActiveUsers,
      unregisterUser,
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
