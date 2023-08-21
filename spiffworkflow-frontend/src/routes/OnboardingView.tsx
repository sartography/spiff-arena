import React, { useEffect, useState } from 'react';
import MDEditor from '@uiw/react-md-editor';
import { useLocation, useNavigate } from 'react-router-dom';
import HttpService from '../services/HttpService';
import { Onboarding } from '../interfaces';
import { objectIsEmpty } from '../helpers';

export default function OnboardingView() {
  const [onboarding, setOnboarding] = useState<Onboarding | null>(null);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    HttpService.makeCallToBackend({
      path: `/onboarding`,
      successCallback: setOnboarding,
    });
  }, [setOnboarding]);

  const onboardingElement = () => {
    if (location.pathname.match(/^\/tasks\/\d+\/\b/)) {
      return null;
    }

    if (
      onboarding &&
      onboarding.type === 'user_input_required' &&
      onboarding.process_instance_id &&
      onboarding.task_id
    ) {
      navigate(
        `/tasks/${onboarding.process_instance_id}/${onboarding.task_id}`
      );
    } else if (
      onboarding &&
      !objectIsEmpty(onboarding) &&
      onboarding.instructions.length > 0
    ) {
      return (
        <div data-color-mode="light">
          <MDEditor.Markdown
            className="onboarding"
            linkTarget="_blank"
            source={onboarding.instructions}
          />
        </div>
      );
    }
    return null;
  };

  return onboardingElement();
}
