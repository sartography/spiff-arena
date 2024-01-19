import TaskRouteTabs from '../components/TaskRouteTabs';
import InProgressInstances from './InProgressInstances';
import OnboardingView from './OnboardingView';

export default function RootRoute() {
  return (
    <>
      <OnboardingView />
      <TaskRouteTabs />
      <InProgressInstances />
    </>
  );
}
