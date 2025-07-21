import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Box, Typography } from '@mui/material';
import { useNavigate } from 'react-router';
import { useTranslation } from 'react-i18next';
import TaskControls from '../components/TaskControls';
import HttpService from '../services/HttpService';
import { ProcessInstanceTask } from '../interfaces';
import HeaderTabs from '../components/HeaderTabs';
import TaskTable from '../components/TaskTable';
import OnboardingView from './OnboardingView';

type HomepageProps = {
  viewMode: 'table' | 'tile';
  setViewMode: React.Dispatch<React.SetStateAction<'table' | 'tile'>>;
  isMobile: boolean;
};

type GroupedItems = {
  [key: string]: ProcessInstanceTask[];
};

function Homepage({ viewMode, setViewMode, isMobile }: HomepageProps) {
  const [lastProcessInstanceId, setLastProcessInstanceId] = useState<
    number | null
  >(null);
  const navigate = useNavigate();
  const [tasks, setTasks] = useState<ProcessInstanceTask[] | null>(null);
  const [groupedTasks, setGroupedTasks] = useState<GroupedItems | null>(null);
  const [selectedGroupBy, setSelectedGroupBy] = useState<string | null>(null);

  const { t } = useTranslation();
  const responsiblePartyLabel = t('responsible_party');
  const processGroupLabel = t('process_group');
  const groupByOptions = useMemo(
    () => [responsiblePartyLabel, processGroupLabel],
    [responsiblePartyLabel, processGroupLabel],
  );

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

  useEffect(() => {
    const storedProcessInstanceId = localStorage.getItem(
      'lastProcessInstanceId',
    );
    if (storedProcessInstanceId) {
      setLastProcessInstanceId(Number(storedProcessInstanceId));
      localStorage.removeItem('lastProcessInstanceId');
    }
  }, []);

  const onGroupBySelect = useCallback(
    (groupBy: string) => {
      if (!tasks) {
        return;
      }
      setSelectedGroupBy(groupBy);

      if (groupBy === processGroupLabel) {
        const grouped = tasks.reduce(
          (acc: GroupedItems, task: ProcessInstanceTask) => {
            const processGroupIdentifier = task.process_model_identifier
              .split('/')
              .slice(0, -1)
              .join('/');
            if (!acc[processGroupIdentifier]) {
              acc[processGroupIdentifier] = [];
            }
            acc[processGroupIdentifier].push(task);
            return acc;
          },
          {},
        );
        setGroupedTasks(grouped);
      } else if (groupBy === '') {
        setGroupedTasks(null);
        setSelectedGroupBy(null);
      } else {
        setSelectedGroupBy(groupBy);
        if (groupBy === responsiblePartyLabel) {
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
      }
    },
    [tasks, processGroupLabel, responsiblePartyLabel],
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
        const isMe = groupName === responsiblePartyMeKey;
        const isProcessGroup = selectedGroupBy === 'Process Group';
        let headerText = t('tasks_for');
        if (!isMe) {
          if (isProcessGroup) {
            headerText = t('tasks_from_process_group');
          } else {
            headerText = t('tasks_for_user_group');
          }
        }
        const groupText = isMe ? t('me') : groupName;
        return (
          <Box key={groupName} sx={{ mb: 2 }}>
            <Typography variant="h4" sx={{ mb: 1 }}>
              {headerText}
              <Box component="span" sx={{ color: 'text.accent' }}>
                {groupText}
              </Box>
            </Typography>
            <TaskTable entries={taskList} viewMode={viewMode} />
          </Box>
        );
      });
    }

    return <TaskTable entries={tasks} viewMode={viewMode} />;
  };

  return (
    <>
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
          <Typography variant="h1">{t('home')}</Typography>
        </Box>
      ) : (
        <Typography variant="h1" sx={{ mb: 2 }}>
          {t('home')}
        </Typography>
      )}
      <OnboardingView />
      {lastProcessInstanceId && !isMobile && (
        <Box
          className="fadeIn"
          sx={{
            position: 'fixed',
            top: 16,
            right: 16,
            bgcolor: 'background.paper',
            boxShadow: 3,
            p: 2,
            borderRadius: 1,
            zIndex: 1300,
          }}
        >
          <Typography variant="h6">{t('last_process_instance')}</Typography>
          <Typography variant="body2">
            {t('id_label')}: {lastProcessInstanceId}
          </Typography>
        </Box>
      )}

      <HeaderTabs
        value={0}
        onChange={(_event, newValue) => {
          if (newValue === 1) {
            navigate('/started-by-me');
          }
        }}
        taskControlElement={
          <TaskControls
            viewMode={viewMode}
            setViewMode={setViewMode}
            groupByOptions={groupByOptions}
            onGroupBySelect={onGroupBySelect}
            selectedGroupBy={selectedGroupBy}
          />
        }
      />
      {taskTableElement()}
    </>
  );
}

export default Homepage;
