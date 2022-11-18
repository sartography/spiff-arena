import { useContext, useEffect, useState } from 'react';
import { Route, Routes, useLocation, useNavigate } from 'react-router-dom';
// @ts-ignore
import { Tabs, TabList, Tab } from '@carbon/react';
import TaskShow from './TaskShow';
import ErrorContext from '../contexts/ErrorContext';
import MyTasks from './MyTasks';
import GroupedTasks from './GroupedTasks';
import CompletedInstances from './CompletedInstances';
import CreateNewInstance from './CreateNewInstance';

export default function HomePageRoutes() {
  const location = useLocation();
  const setErrorMessage = (useContext as any)(ErrorContext)[1];
  const [selectedTabIndex, setSelectedTabIndex] = useState<number>(0);
  const navigate = useNavigate();

  useEffect(() => {
    setErrorMessage(null);
    let newSelectedTabIndex = 0;
    if (location.pathname.match(/^\/tasks\/grouped\b/)) {
      newSelectedTabIndex = 1;
    } else if (location.pathname.match(/^\/tasks\/completed-instances\b/)) {
      newSelectedTabIndex = 2;
    } else if (location.pathname.match(/^\/tasks\/create-new-instance\b/)) {
      newSelectedTabIndex = 3;
    }
    setSelectedTabIndex(newSelectedTabIndex);
  }, [location, setErrorMessage]);

  return (
    <>
      <Tabs selectedIndex={selectedTabIndex}>
        <TabList aria-label="List of tabs">
          <Tab onClick={() => navigate('/tasks/my-tasks')}>My Tasks</Tab>
          <Tab onClick={() => navigate('/tasks/grouped')}>Grouped Tasks</Tab>
          <Tab onClick={() => navigate('/tasks/completed-instances')}>
            Completed Instances
          </Tab>
          <Tab onClick={() => navigate('/tasks/create-new-instance')}>
            Create New Instance +
          </Tab>
        </TabList>
      </Tabs>
      <br />
      <Routes>
        <Route path="/" element={<MyTasks />} />
        <Route path="my-tasks" element={<MyTasks />} />
        <Route path=":process_instance_id/:task_id" element={<TaskShow />} />
        <Route path="grouped" element={<GroupedTasks />} />
        <Route path="completed-instances" element={<CompletedInstances />} />
        <Route path="create-new-instance" element={<CreateNewInstance />} />
      </Routes>
    </>
  );
}
