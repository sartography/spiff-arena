import { DataGrid, GridColDef, GridRowsProp } from '@mui/x-data-grid';
import { useEffect, useState } from 'react';
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
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import TaskCard from '../cards/TaskCard';
import useTaskCollection from '../../../hooks/useTaskCollection';

export default function MyTasks({
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
  const { taskCollection } = useTaskCollection({ processInfo: pi });

  const isDark = useTheme().palette.mode === 'dark';

  const handleGridRowClick = (data: Record<string, any>) => {
    callback(data.row);
  };

  type TabData = { label: string; value: string };
  const handleTabChange = (tab: TabData) => {
    setSelectedTab(tab.value);
  };

  useEffect(() => {
    const filtered =
      filter && taskCollection.results
        ? taskCollection?.results.filter((instance: any) => {
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
                .includes(filter.toLowerCase())
            );
          })
        : [];
    setTaskRows(filtered);
  }, [filter]);

  useEffect(() => {
    const columns = [
      {
        field: 'process_instances',
        headerName: 'Process Instances',
        flex: 1,
        renderCell: (params: Record<string, any>) => <TaskCard task={params} />,
      },
    ];
    if (taskCollection?.results) {
      const rows = [...taskCollection.results].filter(
        (row) => row.process_instance_id === pi.id
      );
      setTaskColumns(columns);
      setTaskRows(rows);
    }
  }, [taskCollection]);

  const tabData = [
    {
      label: `Tasks (${
        pi.id
          ? taskCollection.results?.filter(
              (row: Record<string, any>) => row.process_instance_id === pi.id
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

  // useEffect(() => console.log(pi), [pi]);

  const bgPaper = isDark ? 'background.paper' : 'background.bluegreylight';
  const secondaryText = 'text.secondary';

  return <Box />;
}
