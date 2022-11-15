import { useContext, useEffect, useState } from 'react';
import { Route, Routes, useLocation, useNavigate } from 'react-router-dom';
// @ts-ignore
import { Tabs, TabList, Tab } from '@carbon/react';
import TaskShow from './TaskShow';
import ErrorContext from '../contexts/ErrorContext';
import MyTasks from './MyTasks';
import GroupedTasks from './GroupedTasks';
import CompletedInstances from './CompletedInstances';
import SecretList from './SecretList';
import SecretNew from './SecretNew';
import SecretShow from './SecretShow';
import AuthenticationList from './AuthenticationList';

export default function Configuration() {
  const location = useLocation();
  const setErrorMessage = (useContext as any)(ErrorContext)[1];
  const [selectedTabIndex, setSelectedTabIndex] = useState<number>(0);
  const navigate = useNavigate();

  useEffect(() => {
    setErrorMessage(null);
    let newSelectedTabIndex = 0;
    if (location.pathname.match(/^\/admin\/configuration\/authentications\b/)) {
      newSelectedTabIndex = 1;
    }
    setSelectedTabIndex(newSelectedTabIndex);
  }, [location, setErrorMessage]);

  return (
    <>
      <Tabs selectedIndex={selectedTabIndex}>
        <TabList aria-label="List of tabs">
          <Tab onClick={() => navigate('/admin/configuration/secrets')}>
            Secrets
          </Tab>
          <Tab onClick={() => navigate('/admin/configuration/authentications')}>
            Authentications
          </Tab>
        </TabList>
      </Tabs>
      <br />
      <Routes>
        <Route path="/" element={<SecretList />} />
        <Route path="secrets" element={<SecretList />} />
        <Route path="secrets/new" element={<SecretNew />} />
        <Route path="secrets/:key" element={<SecretShow />} />
        <Route path="authentications" element={<AuthenticationList />} />
      </Routes>
    </>
  );
}
