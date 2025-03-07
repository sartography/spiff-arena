import React, { useMemo } from 'react';
import { Box, Typography } from '@mui/material';
import { useNavigate } from 'react-router';
import TaskControls from '../components/TaskControls';
import useProcessInstances from '../hooks/useProcessInstances';
import HeaderTabs from '../components/HeaderTabs';
import { ReportFilter } from '../interfaces';
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

  // This feature doesn't work and is redundant since a user can use the process instances list page instead.
  // https://github.com/sartography/spiff-arena/issues/2250
  // const [showNonActive, setShowNonActive] = useState(false);

  const additionalReportFilters = useMemo<ReportFilter[]>(() => {
    return [
      {
        field_name: 'with_oldest_open_task',
        field_value: true,
        operator: 'equals',
      },
    ];
  }, []);

  const { processInstances } = useProcessInstances({
    reportIdentifier: 'system_report_in_progress_instances_initiated_by_me',
    additionalReportFilters,
    // autoReload: true,
  });

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
            navigate('/');
          }
        }}
        taskControlElement={
          <TaskControls
            // showNonActive={showNonActive}
            // setShowNonActive={setShowNonActive}
            setViewMode={setViewMode}
            viewMode={viewMode}
          />
        }
      />
      <TaskTable
        entries={processInstances}
        viewMode={viewMode}
        // showNonActive={showNonActive}
      />
    </>
  );
}

export default InstancesStartedByMe;
