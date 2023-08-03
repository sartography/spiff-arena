import React, { useEffect, useState } from 'react';
import MDEditor from '@uiw/react-md-editor';
import HttpService from '../services/HttpService';
import { Onboarding } from '../interfaces';

export default function OnboardingView() {
  const [onboarding, setOnboarding] = useState<Onboarding | null>(null);

  // const navigate = useNavigate();

  useEffect(() => {
    HttpService.makeCallToBackend({
      path: `/onboarding`,
      successCallback: setOnboarding,
    });
  }, [setOnboarding]);

  const onboardingElement = () => {
    if (onboarding && onboarding.instructions.length > 0) {
      return (
        <MDEditor.Markdown
          className="onboarding"
          linkTarget="_blank"
          source={onboarding.instructions}
        />
      );
      /*
      if (onboarding.type === 'default_view') {
        if (onboarding.value === 'my_tasks') {
          return <MyTasks />;
        }
      } else if (
          onboarding.type === 'user_input_required'
      ) {
        console.log("onboarding");
      } else if (
        onboarding.type === 'user_input_required' &&
        onboarding.process_instance_id &&
        onboarding.task_id
      ) {
        navigate(
          `/tasks/${onboarding.process_instance_id}/${onboarding.task_id}`
        );
      }
      */
    }
    return null;
  };

  return onboardingElement();
}
