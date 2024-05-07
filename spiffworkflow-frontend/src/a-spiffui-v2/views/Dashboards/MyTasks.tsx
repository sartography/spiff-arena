import { Box, Chip, Stack } from '@mui/material';
import { DataGrid, GridColDef, GridRowsProp } from '@mui/x-data-grid';
import { useEffect, useState } from 'react';
import ProcessInstanceCard from './ProcessInstanceCard';
import useTaskCollection from '../../hooks/useTaskCollection';

export default function MyTasks({
  filter,
  callback,
}: {
  filter: string;
  callback: (data: Record<string, any>) => void;
}) {
  const { taskCollection } = useTaskCollection();
  const [taskColumns, setTaskColumns] = useState<GridColDef[]>([]);
  const [taskRows, setTaskRows] = useState<GridRowsProp[]>([]);

  /** These values map to theme tokens, which enable the light/dark modes etc. */
  const chipBackground = (params: any) => {
    switch (params.value) {
      case 'Completed':
      case 'complete':
        return 'info';
      case 'Started':
        return 'success';
      case 'error':
        return 'error';
      case 'Wait a second':
      case 'user_input_required':
        return 'warning';
      default:
        return 'default';
    }
  };

  const handleGridRowClick = (data: Record<string, any>) => {
    callback(data.row);
  };

  useEffect(() => {
    const filtered = filter
      ? taskCollection.results.filter((instance: any) => {
          const searchFields = [
            'process_model_display_name',
            'last_milestone_bpmn_name',
            'process_initiator_username',
            'status',
          ];

          return searchFields.some((field) =>
            (instance[field] || '')
              .toString()
              .toLowerCase()
              .includes(filter.toLowerCase())
          );
        })
      : taskCollection.results || [];

    setTaskRows(filtered);
  }, [filter]);

  useEffect(() => {
    if ('results' in taskCollection) {
      const mappedColumns = taskCollection.results.map(
        (task: Record<string, any>) => ({
          field: 'process_model_display_name',
          headerName: task.task_title,
          flex: 1,
        })
      );

      setTaskColumns(mappedColumns);
      setTaskRows([...taskCollection.results]);
    }
  }, [taskCollection]);

  return (
    <>
      <Box
        sx={{
          display: { xs: 'none', lg: 'block' },
          position: 'relative',
        }}
      >
        <DataGrid
          sx={{
            '&, [class^=MuiDataGrid]': { border: 'none' },
          }}
          rows={taskRows}
          columns={taskColumns}
          onRowClick={handleGridRowClick}
        />
      </Box>
      <Box
        sx={{
          display: { xs: 'block', lg: 'none' },
        }}
      >
        <Stack
          gap={2}
          sx={{
            flexDirection: 'row',
            flexWrap: 'wrap',
            justifyContent: 'center',
          }}
        >
          {taskRows.map((instance: Record<string, any>) => (
            <>Hello</> // <ProcessInstanceCard instance={instance} />
          ))}
        </Stack>
      </Box>
    </>
  );
}
