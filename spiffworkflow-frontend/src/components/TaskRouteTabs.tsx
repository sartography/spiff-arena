import { useLocation } from 'react-router-dom';
import { SpiffTab } from '../interfaces';
import SpiffTabs from './SpiffTabs';

export default function TaskRouteTabs() {
  const location = useLocation();
  if (location.pathname.match(/^\/tasks\/\d+\/\b/)) {
    return null;
  }

  const spiffTabs: SpiffTab[] = [
    { path: '/tasks/grouped', display_name: 'In Progress' },
    { path: '/tasks/completed-instances', display_name: 'Completed' },
    { path: '/tasks/create-new-instance', display_name: 'Start New +' },
  ];
  return <SpiffTabs tabs={spiffTabs} />;
}
