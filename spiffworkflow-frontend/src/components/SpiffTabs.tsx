import { ChangeEvent, useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Tabs, Tab } from '@mui/material'; // Importing MUI components
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

  const handleTabChange = (event: ChangeEvent<{}>, newValue: number) => {
    navigate(tabs[newValue].path);
  };

  if (selectedTabIndex !== null && tabs.length > selectedTabIndex) {
    return (
      <>
        <Tabs
          value={selectedTabIndex}
          onChange={handleTabChange}
          aria-label="List of tabs"
        >
          {tabs.map((spiffTab: SpiffTab) => (
            <Tab key={spiffTab.display_name} label={spiffTab.display_name} />
          ))}
        </Tabs>
        <br />
      </>
    );
  }
  return null;
}
