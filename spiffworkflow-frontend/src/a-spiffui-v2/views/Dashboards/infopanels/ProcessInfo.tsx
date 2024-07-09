import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Paper,
  Stack,
  Tab,
  Tabs,
  Typography,
  useTheme,
} from '@mui/material';
import { useEffect, useState } from 'react';
import { DataGrid, GridColDef, GridRowsProp } from '@mui/x-data-grid';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import TaskCard from '../cards/TaskCard';

/**
 * Fed to the InfoPanel to display process info (name etc.) and a list of related Tasks.
 * We have a bit more of an idea how this will work in practice (tasks and milestones both in the list,
 * sorted in chronological order, etc.), but it's still a bit of a placeholder.
 */
export default function ProcessInfo({
  filter,
  callback,
  pi,
}: {
  filter: string;
  callback: (data: Record<string, any>) => void;
  pi: Record<string, any>;
}) {
  const [selectedTab, setSelectedTab] = useState('tasks');
  const [taskColumns, setTaskColumns] = useState<GridColDef[]>([]);
  const [taskRows, setTaskRows] = useState<GridRowsProp[]>([]);

  const isDark = useTheme().palette.mode === 'dark';

  const handleGridRowClick = (data: Record<string, any>) => {
    callback(data.row);
  };

  type TabData = { label: string; value: string };
  const handleTabChange = (tab: TabData) => {
    setSelectedTab(tab.value);
  };

  const tabData = [
    {
      label: `Tasks (${
        pi.id
          ? pi.tasks.filter(
              (row: Record<string, any>) => row.process_instance_id === pi.id,
            ).length
          : '-'
      })`,
      value: 'tasks',
    },
    {
      label: 'Files',
      value: 'files',
    },
    {
      label: 'Metadata',
      value: 'metadata',
    },
    { label: 'Messages', value: 'support' },
  ];

  useEffect(() => {
    if (!filter) {
      return;
    }

    const filtered = pi.tasks?.results
      ? pi.tasks?.results.filter((instance: any) => {
          const searchFields = [
            'process_model_display_name',
            'process_initiator_username',
            'process_instance_status',
            'task_name',
            'task_status',
            'task_title',
            'task_type',
          ];
          return searchFields.some((field) =>
            (instance[field] || '')
              .toString()
              .toLowerCase()
              .includes(filter.toLowerCase()),
          );
        })
      : [];
    setTaskRows(filtered);
  }, [filter, pi.tasks?.results]);

  const columns = [
    {
      field: 'process_instances',
      headerName: 'Process Instances',
      flex: 1,
      renderCell: (params: Record<string, any>) => <TaskCard task={params} />,
    },
  ];

  useEffect(() => {
    if (pi?.id) {
      const rows = [...pi.tasks].filter(
        (row) => row.process_instance_id === pi.id,
      );
      setTaskColumns(columns);
      setTaskRows(rows);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pi]);

  const bgPaper = isDark ? 'background.paper' : 'background.bluegreylight';
  const secondaryText = 'text.secondary';

  return (
    <Stack sx={{ width: '100%' }}>
      <Accordion
        defaultExpanded
        sx={{
          boxShadow: 'none',
          backgroundColor: bgPaper,
          borderBottom: '1px solid',
          borderColor: 'divider',
        }}
      >
        <AccordionSummary
          expandIcon={<ExpandMoreIcon />}
          aria-controls="panel1-content"
          id="panel1-header"
        >
          <Typography color="primary">
            Process Detail: {pi?.process_model_display_name || '--'}
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Stack
            direction="row"
            gap={2}
            sx={{
              backgroundColor: bgPaper,
              paddingRight: 2,
            }}
          >
            <Stack
              sx={{
                height: 180,
                padding: 2,
                flex: 1,
              }}
            >
              <Box sx={{ paddingBottom: 2 }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  {pi?.process_model_display_name}
                </Typography>
                <Typography variant="subtitle1" sx={{ color: secondaryText }}>
                  ID: {pi?.id}
                </Typography>
              </Box>
            </Stack>
            <Stack sx={{ width: '50%', justifyContent: 'center' }}>
              <Paper
                sx={{
                  padding: 1,
                  height: 120,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 1,
                }}
              >
                <Stack>
                  <Typography
                    variant="caption"
                    color="primary"
                    sx={{ fontWeight: 600 }}
                  >
                    {pi?.process_initiator_username}
                  </Typography>
                  <Typography variant="caption" sx={{ color: secondaryText }}>
                    ID: {pi?.id}
                  </Typography>
                </Stack>

                <Typography variant="caption" sx={{ color: secondaryText }}>
                  Status: {pi?.status}
                </Typography>
                <Typography variant="caption" sx={{ color: secondaryText }}>
                  Last milestone: {pi?.last_milestone_bpmn_name}
                </Typography>
              </Paper>
            </Stack>
          </Stack>
        </AccordionDetails>
      </Accordion>
      <Tabs value={selectedTab} variant="fullWidth">
        {tabData.map((tab) => (
          <Tab
            key={tab.value}
            label={tab.label}
            value={tab.value}
            onClick={() => handleTabChange(tab)}
            iconPosition="start"
          />
        ))}
      </Tabs>
      <Box
        sx={{
          width: '100%',
          height: '100%',
          overflowY: 'scroll',
          '&::-webkit-scrollbar': {
            width: '0.5em',
          },
          '&::-webkit-scrollbar-track': {
            boxShadow: 'inset 0 0 6px rgba(0,0,0,0.00)',
            webkitBoxShadow: 'inset 0 0 6px rgba(0,0,0,0.00)',
          },
          '&::-webkit-scrollbar-thumb': {
            backgroundColor: 'background.bluegreymedium',
          },
        }}
      >
        <DataGrid
          autoHeight
          columnHeaderHeight={0}
          getRowHeight={() => 'auto'}
          rows={taskRows}
          columns={taskColumns}
          onRowClick={handleGridRowClick}
          hideFooter
        />
      </Box>
    </Stack>
  );
}
