import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import HttpService from '../services/HttpService';
import InProgressInstances from './InProgressInstances';
import { Onboarding } from '../interfaces';
import MyTasks from './MyTasks';

export default function OnboardingView() {
  const [onboarding, setOnboarding] = useState<Onboarding | null>(null);

  const navigate = useNavigate();

  useEffect(() => {
    HttpService.makeCallToBackend({
      path: `/onboarding`,
      successCallback: setOnboarding,
    });
  }, [setOnboarding]);

  const onboardingElement = () => {
    if (onboarding) {
      if (onboarding.type === 'default_view') {
        if (onboarding.value === 'my_tasks') {
          return <MyTasks />;
        }
      } else if (
        onboarding.type === 'user_input_required' &&
        onboarding.process_instance_id &&
        onboarding.task_id
      ) {
        navigate(
          `/tasks/${onboarding.process_instance_id}/${onboarding.task_id}`
        );
      }
    }

    return <InProgressInstances />;
  };

  return onboardingElement();
}
