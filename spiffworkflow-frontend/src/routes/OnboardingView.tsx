import { useEffect, useState } from 'react';
import HttpService from '../services/HttpService';
import InProgressInstances from './InProgressInstances';

export default function OnboardingView() {
  const [userGroups, setUserGroups] = useState<string[] | null>(null);

  useEffect(() => {
    HttpService.makeCallToBackend({
      path: `/onboarding`,
      successCallback: setUserGroups,
    });
  }, [setUserGroups]);

  return <InProgressInstances />;
}
