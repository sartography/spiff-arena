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
  }, [location, setErrorMessage]);

  // selectedIndex={selectedTabIndex}
  // onChange={(event: any) => {
  //   setSelectedTabIndex(event.selectedIndex);
  // }}
  return (
    <>
      <h1>HELO</h1>
      <Tabs>
        <TabList aria-label="List of tabs">
          <Tab onClick={() => navigate('http://www.google.com')}>
            Tab Label 1
          </Tab>
          <Tab>Tab Label 2</Tab>
          <Tab disabled>Tab Label 3</Tab>
          <Tab title="Tab Label 4 with a very long long title">
            Tab Label 4 with a very long long title
          </Tab>
          <Tab>Tab Label 5</Tab>
        </TabList>
      </Tabs>
      <Routes>
        <Route path="/" element={<MyTasks />} />
        <Route path=":process_instance_id/:task_id" element={<TaskShow />} />
      </Routes>
    </>
  );
}
