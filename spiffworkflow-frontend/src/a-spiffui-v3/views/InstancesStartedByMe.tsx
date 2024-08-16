import React, { useMemo, useState } from 'react';
import { Box, Typography } from '@mui/material';
import { useNavigate } from 'react-router';
import SearchBar from '../components/SearchBar';
import TaskControls from '../components/TaskControls';
import useProcessInstances from '../hooks/useProcessInstances';
import HeaderTabs from '../components/HeaderTabs';
import { ReportFilter } from '../../interfaces';
import TaskTable from '../components/TaskTable';

type InstancesStartedByMeProps = {
  viewMode: 'table' | 'tile';
  setViewMode: React.Dispatch<React.SetStateAction<'table' | 'tile'>>;
  isMobile: boolean;
};

function InstancesStartedByMe({
  viewMode,
  setViewMode,
  isMobile,
}: InstancesStartedByMeProps) {
  const navigate = useNavigate();
  const [showNonActive, setShowNonActive] = useState(false);

  const additionalReportFilters = useMemo<ReportFilter[]>(() => {
    return [
      {
        field_name: 'with_oldest_open_task',
        field_value: true,
      },
    ];
  }, []);

  const { processInstances } = useProcessInstances({
    reportIdentifier: 'system_report_in_progress_instances_initiated_by_me',
    additionalReportFilters,
    // autoReload: true,
  });

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
          showNonActive={showNonActive}
          setShowNonActive={setShowNonActive}
          setViewMode={setViewMode}
          viewMode={viewMode}
        />
      </Box>
      <TaskTable
        entries={processInstances}
        viewMode={viewMode}
        showNonActive={showNonActive}
      />
    </Box>
  );
}

export default InstancesStartedByMe;
