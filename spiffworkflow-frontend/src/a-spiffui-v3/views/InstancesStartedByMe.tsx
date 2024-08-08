import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Tabs,
  Tab,
  TextField,
  Select,
  MenuItem,
  Checkbox,
  FormControlLabel,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Button,
  Chip,
} from '@mui/material';
import SearchBar from '../components/SearchBar';
import TaskControls from '../components/TaskControls';
import TaskTableWrapper from '../components/TaskTableWrapper';
import { useNavigate } from 'react-router';
import HttpService from '../../services/HttpService';
import DateAndTimeService from '../../services/DateAndTimeService';
import useProcessInstances from '../../hooks/useProcessInstances';
import TaskTable from '../components/TaskTable';
import HeaderTabs from '../components/HeaderTabs';

const mainBlue = 'primary.main';

function InstancesStartedByMe() {
  const navigate = useNavigate();
  const [hideCompleted, setHideCompleted] = useState(false);
  const { processInstances, pagination, reportMetadata } = useProcessInstances(
    'system_report_in_progress_instances_initiated_by_me',
    undefined,
    'open_instances_started_by_me',
    [2, 5, 25],
    true,
  );

  const getWaitingForTableCellComponent = (
    processInstanceTask: ProcessInstanceTask,
  ) => {
    let fullUsernameString = '';
    let shortUsernameString = '';
    if (processInstanceTask.potential_owner_usernames) {
      fullUsernameString = processInstanceTask.potential_owner_usernames;
      const usernames =
        processInstanceTask.potential_owner_usernames.split(',');
      const firstTwoUsernames = usernames.slice(0, 2);
      if (usernames.length > 2) {
        firstTwoUsernames.push('...');
      }
      shortUsernameString = firstTwoUsernames.join(',');
    }
    if (processInstanceTask.assigned_user_group_identifier) {
      fullUsernameString = processInstanceTask.assigned_user_group_identifier;
      shortUsernameString = processInstanceTask.assigned_user_group_identifier;
    }
    return <span title={fullUsernameString}>{shortUsernameString}</span>;
  };

  const handleRunTask = (processInstanceTask: ProcessInstanceTask) => {
    const taskUrl = `/tasks/${processInstanceTask.process_instance_id}/${processInstanceTask.task_id}`;
    navigate(taskUrl);
  };


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
        value={1}
        onChange={(event, newValue) => {
          if (newValue === 0) {
            navigate('/newui');
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
        <TaskControls hideCompleted={hideCompleted} setHideCompleted={setHideCompleted} />
      </Box>
      <TaskTableWrapper
        tasks={processInstances}
        handleRunTask={handleRunTask}
        getWaitingForTableCellComponent={getWaitingForTableCellComponent}
      />
    </Box>
  );
}

export default InstancesStartedByMe;
