import React, { useCallback, useEffect, useState } from 'react';
import { Box, Typography } from '@mui/material';
import { useNavigate } from 'react-router';
import SearchBar from '../components/SearchBar';
import TaskControls from '../components/TaskControls';
import HttpService from '../../services/HttpService';
import { ProcessInstanceTask } from '../../interfaces';
import HeaderTabs from '../components/HeaderTabs';
import TaskTable from '../components/TaskTable';

type HomepageProps = {
  viewMode: 'table' | 'tile';
  setViewMode: React.Dispatch<React.SetStateAction<'table' | 'tile'>>;
};

function Homepage({ viewMode, setViewMode }: HomepageProps) {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState<ProcessInstanceTask[] | null>(null);
  const [userGroups, setUserGroups] = useState<string[] | null>(null);

  useEffect(() => {
    const getTasks = () => {
      const setTasksFromResult = (result: any) => {
        setTasks(result.results);
      };
      HttpService.makeCallToBackend({
        path: '/tasks',
        successCallback: setTasksFromResult,
      });
      HttpService.makeCallToBackend({
        path: `/user-groups/for-current-user`,
        successCallback: setUserGroups,
      });
    };
    getTasks();
  }, []);

  const onUserGroupSelect = useCallback((userGroup: string) => {
    console.log('userGroup', userGroup);
  }, []);

  return (
    <Box
      component="main"
      sx={{
        flexGrow: 1,
        p: 3,
        overflow: 'auto',
        height: '100vh',
      }}
    >
      <Typography variant="h1" sx={{ mb: 2 }}>
        Home
      </Typography>
      <HeaderTabs
        value={0}
        onChange={(_event, newValue) => {
          if (newValue === 1) {
            navigate('/newui/started-by-me');
          }
        }}
      />
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 2,
        }}
      >
        <SearchBar />
        <TaskControls
          viewMode={viewMode}
          setViewMode={setViewMode}
          userGroups={userGroups}
          onUserGroupSelect={onUserGroupSelect}
        />
      </Box>
      <TaskTable entries={tasks} viewMode={viewMode} />
    </Box>
  );
}

export default Homepage;
