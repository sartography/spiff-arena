import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import HttpService from '../services/HttpService';
import { Onboarding } from '../interfaces';
import { objectIsEmpty } from '../helpers';
import MarkdownRenderer from '../components/MarkdownRenderer';

export default function OnboardingView() {
  const [onboarding, setOnboarding] = useState<Onboarding | null>(null);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    if (location.pathname.match(/^\/tasks\/\d+\//)) {
      return;
    }
    HttpService.makeCallToBackend({
      path: `/onboarding`,
      successCallback: setOnboarding,
    });
  }, [setOnboarding, location.pathname]);

  const onboardingElement = () => {
    if (location.pathname.match(/^\/tasks\/\d+\//)) {
      return null;
    }

    if (
      onboarding &&
      onboarding.type === 'user_input_required' &&
      onboarding.process_instance_id &&
      onboarding.task_id
    ) {
      navigate(
        `/tasks/${onboarding.process_instance_id}/${onboarding.task_id}`,
      );
    } else if (
      onboarding &&
      !objectIsEmpty(onboarding) &&
      onboarding.instructions.length > 0
    ) {
      return (
        <MarkdownRenderer
          className="onboarding"
          linkTarget="_blank"
          source={onboarding.instructions}
        />
      );
    }
    return null;
  };

  return onboardingElement();
}
