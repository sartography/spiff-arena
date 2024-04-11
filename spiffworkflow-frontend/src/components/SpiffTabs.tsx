import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Tabs, TabList, Tab } from '@carbon/react';
import { SpiffTab } from '../interfaces';

type OwnProps = {
  tabs: SpiffTab[];
};

export default function SpiffTabs({ tabs }: OwnProps) {
  const location = useLocation();
  const [selectedTabIndex, setSelectedTabIndex] = useState<number | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    let newSelectedTabIndex = tabs.findIndex((spiffTab: SpiffTab) => {
      return location.pathname === spiffTab.path;
    });
    if (newSelectedTabIndex === -1) {
      newSelectedTabIndex = 0;
    }
    setSelectedTabIndex(newSelectedTabIndex);
  }, [location, tabs]);

  const tabComponents = tabs.map((spiffTab: SpiffTab) => {
    return (
      <Tab onClick={() => navigate(spiffTab.path)}>{spiffTab.display_name}</Tab>
    );
  });

  if (selectedTabIndex !== null && tabComponents.length > selectedTabIndex) {
    return (
      <>
        <Tabs selectedIndex={selectedTabIndex}>
          <TabList aria-label="List of tabs">{tabComponents}</TabList>
        </Tabs>
        <br />
      </>
    );
  }
  return null;
}
