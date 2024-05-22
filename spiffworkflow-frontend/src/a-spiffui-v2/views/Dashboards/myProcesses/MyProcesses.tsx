import {
  DataGrid,
  GridColDef,
  GridRowProps,
  GridRowsProp,
} from '@mui/x-data-grid';
import { useEffect, useState } from 'react';
import { Box } from '@mui/material';
import ProcessInstanceCard from '../cards/ProcessInstanceCard';
import useTaskCollection from '../../../hooks/useTaskCollection';

export default function MyProcesses({
  filter,
  callback,
  pis,
}: {
  filter: string;
  callback: (data: Record<string, any>) => void;
  pis: Record<string, any>;
}) {
  // TODO: Type of this doesn't seem to be ProcessInstance
  // Find out and remove "any""
  const [processInstanceColumns, setProcessInstanceColumns] = useState<
    GridColDef[]
  >([]);
  /** Did this to accommodate adding task counts to the type */
  const [processInstanceRows, setProcessInstanceRows] = useState<
    (GridRowsProp | Record<string, any>)[]
  >([]);

  const { taskCollection } = useTaskCollection({ processInfo: {} });

  const handleGridRowClick = (data: Record<string, any>) => {
    callback(data.row);
  };

  useEffect(() => {
    const filtered =
      filter && pis.results
        ? pis.results.filter((instance: any) => {
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
        : pis.results || [];

    setProcessInstanceRows(filtered);
  }, [filter]);

  // Do a default sort by number of tasks
  const addTaskCounts = (rows: GridRowsProp[]) => {
    const mappedRows = rows.map((row: Record<string, any>) => {
      const taskCount: number = taskCollection?.results?.filter(
        (task: Record<string, any>) => task.process_instance_id === row.id
      ).length;
      return { ...row, taskCount };
    });

    // Throw in a default sort by tasks
    return mappedRows.sort((a, b) => b.taskCount - a.taskCount);
  };

  useEffect(() => {
    if (pis?.report_metadata && taskCollection?.results) {
      const columns = [
        {
          field: 'process_instances',
          headerName: 'Process Instances',
          flex: 1,
          renderCell: (params: Record<string, any>) => (
            <ProcessInstanceCard pi={params} />
          ),
        },
      ];
      setProcessInstanceColumns(columns);
      setProcessInstanceRows(addTaskCounts(pis.results));
    }
  }, [pis]);

  return (
    <Box
      sx={{
        width: '100%',
        height: '100%',
        overflowY: 'auto',
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
        rows={processInstanceRows as GridRowProps[]}
        columns={processInstanceColumns}
        onRowClick={handleGridRowClick}
        hideFooter
      />
    </Box>
  );
}
