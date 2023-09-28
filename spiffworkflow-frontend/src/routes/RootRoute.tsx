import InProgressInstances from './InProgressInstances';
import OnboardingView from './OnboardingView';
import TaskRouteTabs from '../components/TaskRouteTabs';

export default function RootRoute() {
  return (
    <>
      <OnboardingView />
      <TaskRouteTabs />
      <InProgressInstances />
    </>
  );
}
