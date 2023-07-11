import { useEffect, useState } from 'react';
import HttpService from '../services/HttpService';
import InProgressInstances from './InProgressInstances';
import { Onboarding } from '../interfaces';
import MyTasks from './MyTasks';

export default function OnboardingView() {
  const [onboarding, setOnboarding] = useState<Onboarding | null>(null);

  useEffect(() => {
    HttpService.makeCallToBackend({
      path: `/onboarding`,
      successCallback: setOnboarding,
    });
  }, [setOnboarding]);

  const onboardingElement = () => {
    if (onboarding && onboarding.type === "default_view") {
      if (onboarding.value === "my_tasks") {
        return <MyTasks />;
      }
    }
    
    return <InProgressInstances />;
  }

  return onboardingElement();
}
