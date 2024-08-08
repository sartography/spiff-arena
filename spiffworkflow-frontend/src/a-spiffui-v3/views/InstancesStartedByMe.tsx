import React, { useMemo, useState } from 'react';
import { Box, Typography } from '@mui/material';
import { useNavigate } from 'react-router';
import SearchBar from '../components/SearchBar';
import TaskControls from '../components/TaskControls';
import useProcessInstances from '../../hooks/useProcessInstances';
import HeaderTabs from '../components/HeaderTabs';
import {
  ProcessInstance,
  ProcessInstanceTask,
  ReportFilter,
} from '../../interfaces';
import TaskTable from '../components/TaskTable';

function InstancesStartedByMe() {
  const navigate = useNavigate();
  const [hideCompleted, setHideCompleted] = useState(false);

  const additionalReportFilters = useMemo<ReportFilter[]>(() => {
    return [
      {
        field_name: 'with_oldest_open_task',
        field_value: true,
      },
    ];
  }, []);

  const { processInstances, pagination, reportMetadata } = useProcessInstances({
    reportIdentifier: 'system_report_in_progress_instances_initiated_by_me',
    paginationQueryParamPrefix: 'open_instances_started_by_me',
    additionalReportFilters,
    // autoReload: true,
  });

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

  const handleRunTask = (processInstance: ProcessInstance) => {
    const taskUrl = `/tasks/${processInstance.id}/${processInstance.task_id}`;
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
        onChange={(_event, newValue) => {
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
        <TaskControls
          hideCompleted={hideCompleted}
          setHideCompleted={setHideCompleted}
        />
      </Box>
      <TaskTable
        tasks={processInstances}
        handleRunTask={handleRunTask}
        getWaitingForTableCellComponent={getWaitingForTableCellComponent}
      />
    </Box>
  );
}

export default InstancesStartedByMe;
