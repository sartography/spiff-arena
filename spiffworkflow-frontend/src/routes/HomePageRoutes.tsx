import { useContext, useEffect, useState } from 'react';
import { Route, Routes, useLocation, useNavigate } from 'react-router-dom';
// @ts-ignore
import { Tabs, TabList, Tab } from '@carbon/react';
import TaskShow from './TaskShow';
import ErrorContext from '../contexts/ErrorContext';
import MyTasks from './MyTasks';
import TasksForMyOpenProcesses from './TasksForMyOpenProcesses';

export default function HomePageRoutes() {
  const location = useLocation();
  const setErrorMessage = (useContext as any)(ErrorContext)[1];
  const [selectedTabIndex, setSelectedTabIndex] = useState<number>(0);
  const navigate = useNavigate();

  useEffect(() => {
    setErrorMessage(null);
    let newSelectedTabIndex = 0;
    if (location.pathname.match(/^\/tasks\/for-my-open-processes/)) {
      newSelectedTabIndex = 1;
    }
    setSelectedTabIndex(newSelectedTabIndex);
  }, [location, setErrorMessage]);

  return (
    <>
      <Tabs selectedIndex={selectedTabIndex}>
        <TabList aria-label="List of tabs">
          <Tab onClick={() => navigate('/tasks/my-tasks')}>My Tasks</Tab>
          <Tab onClick={() => navigate('/tasks/for-my-open-processes')}>
            Tasks for My Open Processes
          </Tab>
        </TabList>
      </Tabs>
      <br />
      <Routes>
        <Route path="/" element={<MyTasks />} />
        <Route path="my-tasks" element={<MyTasks />} />
        <Route path=":process_instance_id/:task_id" element={<TaskShow />} />
        <Route
          path="for-my-open-processes"
          element={<TasksForMyOpenProcesses />}
        />
      </Routes>
    </>
  );
}
