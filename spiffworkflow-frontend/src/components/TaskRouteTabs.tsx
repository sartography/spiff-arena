import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Tabs, TabList, Tab } from '@carbon/react';

export default function TaskRouteTabs() {
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
}
