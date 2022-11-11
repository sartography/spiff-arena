import { useContext, useEffect, useState } from 'react';
import { Route, Routes, useLocation, useNavigate } from 'react-router-dom';
// @ts-ignore
import { Tabs, TabList, Tab } from '@carbon/react';
import TaskShow from './TaskShow';
import ErrorContext from '../contexts/ErrorContext';
import MyTasks from './MyTasks';

export default function HomePageRoutes() {
  const location = useLocation();
  const setErrorMessage = (useContext as any)(ErrorContext)[1];
  const [selectedTabIndex, setSelectedTabIndex] = useState<number>(0);
  const navigate = useNavigate();

  useEffect(() => {
    setErrorMessage(null);
    let newSelectedTabIndex = 0;
    if (location.pathname.match(/^\/tasks\/\d/)) {
      newSelectedTabIndex = 1;
    }
    setSelectedTabIndex(newSelectedTabIndex);
  }, [location, setErrorMessage]);

  return (
    <>
      <Tabs
        selectedIndex={selectedTabIndex}
        onChange={(event: any) => {
          setSelectedTabIndex(event.selectedIndex);
        }}
      >
        <TabList aria-label="List of tabs">
          <Tab onClick={() => navigate('/tasks/my-tasks')}>My Tasks</Tab>
          <Tab
            onClick={() =>
              navigate('/tasks/9/4dc9f6e3-2256-47b2-9f78-6bc2f061db80')
            }
          >
            One Task
          </Tab>
        </TabList>
      </Tabs>
      <br />
      <Routes>
        <Route path="/" element={<MyTasks />} />
        <Route path="/my-tasks" element={<MyTasks />} />
        <Route path=":process_instance_id/:task_id" element={<TaskShow />} />
      </Routes>
    </>
  );
}
