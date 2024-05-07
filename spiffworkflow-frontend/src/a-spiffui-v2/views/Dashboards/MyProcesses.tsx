import { Box, Chip, Stack } from '@mui/material';
import { DataGrid, GridColDef, GridRowsProp } from '@mui/x-data-grid';
import { useEffect, useState } from 'react';
import ProcessInstanceCard from './ProcessInstanceCard';
import useProcessInstanceCollection from '../../hooks/useProcessInstanceCollection';

export default function MyProcesses({
  filter,
  callback,
}: {
  filter: string;
  callback: (data: Record<string, any>) => void;
}) {
  const { processInstanceCollection } = useProcessInstanceCollection();
  // TODO: Type of this doesn't seem to be ProcessInstance
  // Find out and remove "any""
  const [processInstanceColumns, setProcessInstanceColumns] = useState<
    GridColDef[]
  >([]);
  const [processInstanceRows, setProcessInstanceRows] = useState<
    GridRowsProp[]
  >([]);

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
      ? processInstanceCollection.results.filter((instance: any) => {
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
      : processInstanceCollection.results || [];

    setProcessInstanceRows(filtered);
  }, [filter]);

  useEffect(() => {
    if ('report_metadata' in processInstanceCollection) {
      const mappedColumns =
        processInstanceCollection.report_metadata?.columns.map(
          (column: Record<string, any>) => ({
            field: column.accessor,
            headerName: column.Header,
            flex: (() => {
              // Adjust the width of some columns to clean up UI
              switch (column.Header) {
                case 'Id':
                  return 0.5;
                case 'Start':
                case 'End':
                  return 0.75;
                default:
                  return 1;
              }
            })(),
            renderCell:
              column.Header === 'Last milestone' || column.Header === 'Status'
                ? (params: Record<string, any>) => (
                    <Chip
                      label={params.value || '...no info...'}
                      variant="filled"
                      color={chipBackground(params)}
                      sx={{
                        width: '100%',
                      }}
                    />
                  )
                : null,
          })
        );

      setProcessInstanceColumns(mappedColumns);
      setProcessInstanceRows([...processInstanceCollection.results]);
    }
  }, [processInstanceCollection]);

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
          rows={processInstanceRows}
          columns={processInstanceColumns}
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
          {processInstanceRows.map((instance: Record<string, any>) => (
            <ProcessInstanceCard instance={instance} />
          ))}
        </Stack>
      </Box>
    </>
  );
}
