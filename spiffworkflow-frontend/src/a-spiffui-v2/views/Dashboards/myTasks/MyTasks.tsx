import { DataGrid, GridColDef, GridRowsProp } from '@mui/x-data-grid';
import { useEffect, useState } from 'react';
import ProcessInstanceCard from '../cards/ProcessInstanceCard';

export default function MyProcesses({
  filter,
  callback,
  tasks,
}: {
  filter: string;
  callback: (data: Record<string, any>) => void;
  tasks: Record<string, any>;
}) {
  // TODO: Type of this doesn't seem to be ProcessInstance
  // Find out and remove "any""
  const [columns, setColumns] = useState<GridColDef[]>([]);
  const [rows, setRows] = useState<GridRowsProp[]>([]);

  const handleGridRowClick = (data: Record<string, any>) => {
    callback(data.row);
  };

  useEffect(() => {
    const filtered =
      filter && tasks.results
        ? tasks.results.filter((instance: any) => {
            console.log(tasks.results);
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
        : tasks.results || [];

    setRows(filtered);
  }, [filter]);

  useEffect(() => {
    if ('report_metadata' in tasks) {
      const dgColumns = [
        {
          field: 'tasks',
          headerName: 'Tasks',
          flex: 1,
          renderCell: (params: Record<string, any>) => <TaskCard pi={params} />,
        },
      ];
      setColumns(dgColumns);
      setRows([...tasks.results]);
    }
  }, [tasks]);

  return (
    <DataGrid
      autoHeight
      columnHeaderHeight={0}
      getRowHeight={() => 'auto'}
      rows={rows}
      columns={columns}
      onRowClick={handleGridRowClick}
    />
  );
}
