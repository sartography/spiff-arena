import { useEffect, useState } from 'react';
import { Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { Tabs, TabList, Tab } from '@carbon/react';
import TaskShow from './TaskShow';
import MyTasks from './MyTasks';
import CompletedInstances from './CompletedInstances';
import CreateNewInstance from './CreateNewInstance';
import InProgressInstances from './InProgressInstances';
import OnboardingView from './OnboardingView';

export default function HomePageRoutes() {
  const location = useLocation();
  const [selectedTabIndex, setSelectedTabIndex] = useState<number>(0);
  const navigate = useNavigate();

  useEffect(() => {
    // Do not remove errors here, or they always get removed.
    let newSelectedTabIndex = 0;
    if (location.pathname.match(/^\/tasks\/completed-instances\b/)) {
      newSelectedTabIndex = 1;
    } else if (location.pathname.match(/^\/tasks\/create-new-instance\b/)) {
      newSelectedTabIndex = 2;
    }
    setSelectedTabIndex(newSelectedTabIndex);
  }, [location]);

  const renderTabs = () => {
    if (location.pathname.match(/^\/tasks\/\d+\/\b/)) {
      return null;
    }
    return (
      <>
        <Tabs selectedIndex={selectedTabIndex}>
          <TabList aria-label="List of tabs">
            {/* <Tab onClick={() => navigate('/tasks/my-tasks')}>My Tasks</Tab> */}
            <Tab onClick={() => navigate('/tasks/grouped')}>In Progress</Tab>
            <Tab onClick={() => navigate('/tasks/completed-instances')}>
              Completed
            </Tab>
            <Tab onClick={() => navigate('/tasks/create-new-instance')}>
              Start New +
            </Tab>
          </TabList>
        </Tabs>
        <br />
      </>
    );
  };

  return (
    <div className="fixed-width-container">
      <OnboardingView />
      {renderTabs()}
      <Routes>
        <Route path="/" element={<InProgressInstances />} />
        <Route path="my-tasks" element={<MyTasks />} />
        <Route path=":process_instance_id/:task_id" element={<TaskShow />} />
        <Route path="grouped" element={<InProgressInstances />} />
        <Route path="completed-instances" element={<CompletedInstances />} />
        <Route path="create-new-instance" element={<CreateNewInstance />} />
      </Routes>
    </div>
  );
}
