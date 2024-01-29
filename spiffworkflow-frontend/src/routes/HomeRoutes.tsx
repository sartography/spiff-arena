import { Route, Routes } from 'react-router-dom';
import TaskShow from './TaskShow';
import MyTasks from './MyTasks';
import CompletedInstances from './CompletedInstances';
import CreateNewInstance from './CreateNewInstance';
import InProgressInstances from './InProgressInstances';
import OnboardingView from './OnboardingView';
import TaskRouteTabs from '../components/TaskRouteTabs';

export default function HomeRoutes() {
  return (
    <>
      <OnboardingView />
      <TaskRouteTabs />
      <Routes>
        <Route path="/" element={<InProgressInstances />} />
        <Route path="my-tasks" element={<MyTasks />} />
        <Route path=":process_instance_id/:task_id" element={<TaskShow />} />
        <Route path="in-progress" element={<InProgressInstances />} />
        <Route path="completed-instances" element={<CompletedInstances />} />
        <Route path="create-new-instance" element={<CreateNewInstance />} />
      </Routes>
    </>
  );
}
