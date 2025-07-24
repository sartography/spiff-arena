import { useEffect, useState } from 'react';
import { Avatar, Box } from '@mui/material'; // Import MUI components
import { useTranslation } from 'react-i18next';

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
  const { t } = useTranslation();
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
  }, []); // it is critical to only run this once.

  // activeUsers is supposed to be an array, but it is based on the response body
  // from a network call, so who knows what might happen. Be safe.
  if (!activeUsers.map) {
    return null;
  }

  const au = activeUsers.map((activeUser: User) => {
    return (
      <Avatar
        title={t('also_viewing_this_page', { username: activeUser.username })}
        sx={{ bgcolor: 'primary.main', margin: 1 }} // MUI styling
      >
        {activeUser.username.charAt(0).toUpperCase()}
      </Avatar>
    );
  });
  return (
    <Box display="flex" className="user-list">
      {au}
    </Box>
  ); // MUI Box for layout
}
