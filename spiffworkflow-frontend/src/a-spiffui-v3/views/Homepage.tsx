import React, { useEffect, useState } from 'react';
import { Box, Typography } from '@mui/material';
import { useNavigate } from 'react-router';
import SearchBar from '../components/SearchBar';
import TaskControls from '../components/TaskControls';
import HttpService from '../../services/HttpService';
import { ProcessInstanceTask } from '../../interfaces';
import HeaderTabs from '../components/HeaderTabs';
import TaskTable from '../components/TaskTable';

function Homepage() {
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState<'table' | 'tile'>('table');
  const [tasks, setTasks] = useState<ProcessInstanceTask[] | null>(null);

  useEffect(() => {
    const getTasks = () => {
      const setTasksFromResult = (result: any) => {
        setTasks(result.results);
      };
      HttpService.makeCallToBackend({
        path: '/tasks',
        successCallback: setTasksFromResult,
      });
    };
    getTasks();
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
        <TaskControls setViewMode={setViewMode} viewMode={viewMode} />
      </Box>
      <TaskTable entries={tasks} viewMode={viewMode} />
    </Box>
  );
}

export default Homepage;