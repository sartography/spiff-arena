import React, { useCallback, useEffect, useMemo, useState } from 'react';
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
  isMobile: boolean;
};

type GroupedItems = {
  [key: string]: ProcessInstanceTask[];
};

function Homepage({ viewMode, setViewMode, isMobile }: HomepageProps) {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState<ProcessInstanceTask[] | null>(null);
  const [groupedTasks, setGroupedTasks] = useState<GroupedItems | null>(null);
  const [selectedGroupBy, setSelectedGroupBy] = useState<string | null>(null);

  const groupByOptions = useMemo(() => ['Responsible party'], []);

  const responsiblePartyMeKey = 'spiff_synthetic_key_indicating_assigned_to_me';

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

  const onGroupBySelect = useCallback(
    (groupBy: string) => {
      if (!tasks) {
        return;
      }
      setSelectedGroupBy(groupBy);
      if (groupBy === 'Responsible party') {
        const grouped = tasks.reduce(
          (acc: GroupedItems, task: ProcessInstanceTask) => {
            const key =
              task.assigned_user_group_identifier || responsiblePartyMeKey;
            if (!acc[key]) {
              acc[key] = [];
            }
            acc[key].push(task);
            return acc;
          },
          {},
        );
        setGroupedTasks(grouped);
      }
    },
    [tasks],
  );

  const taskTableElement = () => {
    if (!tasks) {
      return null;
    }

    if (groupedTasks) {
      const specialKeyToSortFirst = responsiblePartyMeKey;
      const sortedKeys = Object.keys(groupedTasks).sort((a, b) => {
        if (a === specialKeyToSortFirst) {
          return -1;
        }
        if (b === specialKeyToSortFirst) {
          return 1;
        }
        return a.localeCompare(b); // Alphabetical order for the rest
      });
      return sortedKeys.map((groupName: string) => {
        const taskList = groupedTasks[groupName];
        const tableName =
          groupName === responsiblePartyMeKey ? 'Me' : groupName;
        return (
          <>
            <h1>{tableName}</h1>
            <TaskTable entries={taskList} viewMode={viewMode} />
          </>
        );
      });
    }

    return <TaskTable entries={tasks} viewMode={viewMode} />;
  };

  return (
    <Box
      component="main"
      sx={{
        flexGrow: 1,
        p: 3,
        overflow: 'auto',
        height: isMobile ? 'calc(100vh - 64px)' : '100vh',
        mt: isMobile ? '64px' : 0,
      }}
    >
      {isMobile ? (
        <Box
          sx={{
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100%',
            zIndex: 1300,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            bgcolor: 'background.default',
            p: 2,
            boxShadow: 1,
          }}
        >
          <Typography variant="h1" sx={{ fontSize: '1.5rem' }}>
            Home
          </Typography>
        </Box>
      ) : (
        <Typography variant="h1" sx={{ mb: 2 }}>
          Home
        </Typography>
      )}
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
          groupByOptions={groupByOptions}
          onGroupBySelect={onGroupBySelect}
          selectedGroupBy={selectedGroupBy}
        />
      </Box>
      {taskTableElement()}
    </Box>
  );
}

export default Homepage;
