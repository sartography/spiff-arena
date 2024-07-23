import {
  DataGrid,
  GridColDef,
  GridRowProps,
  GridRowsProp,
} from '@mui/x-data-grid';
import { useCallback, useEffect, useState } from 'react';
import { Box } from '@mui/material';
import ProcessInstanceCard from '../cards/ProcessInstanceCard';
import useTaskCollection from '../../../hooks/useTaskCollection';
import CellRenderer from './CellRenderer';

/** Show the user a list of Processes, with the ability to filter them. */
export default function MyProcesses({
  filter,
  callback,
  pis,
}: {
  filter: string;
  callback: (data: Record<string, any>) => void;
  pis: Record<string, any>;
}) {
  const [processInstanceColumns, setProcessInstanceColumns] = useState<
    GridColDef[]
  >([]);
  /** Did this to accommodate adding task counts to the type */
  const [mappedRows, setMappedRows] = useState<
    (GridRowsProp | Record<string, any>)[]
  >([]);
  const [filteredRows, setFilteredRows] = useState<
    (GridRowsProp | Record<string, any>)[]
  >([]);

  const { taskCollection } = useTaskCollection({ processInfo: {} });

  const handleGridRowClick = (data: Record<string, any>) => {
    callback(data.row);
  };

  useEffect(() => {
    const filtered = filter
      ? mappedRows.filter((instance: any) => {
          /** Not really sure what to search at this time, so use these fields to display something */
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
              .includes(filter.toLowerCase()),
          );
        })
      : mappedRows || [];

    /**
     * If you don't want to sort by task count, you can remove this block
     * Also note that spreading the filtered array is necessary to avoid mutating state.
     */
    const sorted = [...filtered].sort(
      (a: Record<string, any>, b: Record<string, any>) => {
        return b.taskCount - a.taskCount;
      },
    );
    setFilteredRows(sorted);
  }, [filter, mappedRows]);

  // Put the task objects right on the process instance objects
  const addTaskCounts = useCallback(
    (rows: GridRowsProp[]) => {
      return rows.map((row: Record<string, any>) => {
        const tasks = taskCollection?.results?.filter(
          (task: Record<string, any>) => task.process_instance_id === row.id,
        );
        return { ...row, tasks };
      });
    },
    [taskCollection?.results],
  );

  useEffect(() => {
    if (pis?.report_metadata && taskCollection?.results) {
      const mappedColumns = pis.report_metadata?.columns.map(
        (column: Record<string, any>) => ({
          field: column.accessor,
          headerName: column.Header,
          colSpan: 0,
          flex: 1,
          renderCell: (params: Record<string, any>) => {
            return <CellRenderer header={column.Header} data={params} />;
          },
        }),
      );

      /**
       * Prepend the "Lead" field, which is technically a card.
       * It satisfies the design requirement.
       */
      const columns = [
        {
          field: 'processes',
          headerName: 'Processes',
          flex: 2,
          renderCell: (params: Record<string, any>) => (
            <ProcessInstanceCard pi={params} />
          ),
        },
        ...mappedColumns,
      ];

      setProcessInstanceColumns(columns);
      const rows = addTaskCounts(pis.results);
      setMappedRows(rows);
      setFilteredRows(
        [...rows].sort((a, b) => b.tasks.length - a.tasks.length),
      );
    }
  }, [pis, addTaskCounts, taskCollection?.results]);

  return (
    <Box
      sx={{
        width: '100%',
        height: '100%',
        overflowY: 'auto',
      }}
    >
      <DataGrid
        sx={{
          '& .MuiDataGrid-cell:focus': {
            outline: 'none',
          },
        }}
        initialState={{
          columns: {
            columnVisibilityModel: {
              status: false,
              last_milestone_bpmn_name: false,
            },
          },
        }}
        autoHeight
        getRowHeight={() => 'auto'}
        rows={filteredRows as GridRowProps[]}
        columns={processInstanceColumns}
        onRowClick={handleGridRowClick}
        hideFooter
      />
    </Box>
  );
}
