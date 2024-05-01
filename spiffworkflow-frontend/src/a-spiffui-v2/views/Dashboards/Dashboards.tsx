import {
  Box,
  Chip,
  FormControl,
  Grid,
  InputAdornment,
  InputLabel,
  ListItemIcon,
  ListItemText,
  MenuItem,
  Select,
  SelectChangeEvent,
  Stack,
  Tab,
  Tabs,
  TextField,
} from '@mui/material';
import { ReactNode, useEffect, useState } from 'react';
import Inventory2OutlinedIcon from '@mui/icons-material/Inventory2Outlined';
import MonetizationOnOutlinedIcon from '@mui/icons-material/MonetizationOnOutlined';
import GroupsIcon from '@mui/icons-material/Groups';
import FilterAltOutlinedIcon from '@mui/icons-material/FilterAltOutlined';
import SearchOutlinedIcon from '@mui/icons-material/SearchOutlined';
import { DataGrid, GridRowsProp, GridColDef } from '@mui/x-data-grid';
import { blue, grey, red, yellow } from '@mui/material/colors';
import Columns from '../../assets/icons/columns-2.svg';
import Share from '../../assets/icons/share-arrow.svg';
import GridIcon from '../../assets/icons/grid.svg';
import Download from '../../assets/icons/download.svg';
import Toolbar from './Toolbar';
import FilterCard from './FilterCard';
import useProcessInstances from '../../hooks/useProcessInstances';
import { wrap } from 'module';

export default function Dashboards() {
  const [selectedTab, setSelectedTab] = useState('myProcesses');
  const [selectedFilter, setSelectedFilter] = useState('new');
  // TODO: Type of this doesn't seem to be ProcessInstance
  // Find out and remove "any""
  const [processInstanceColumns, setProcessInstanceColumns] = useState<
    Record<string, any>
  >({});

  const { processInstances } = useProcessInstances();

  const tabData = [
    {
      label: 'My Processes',
      value: 'myProcesses',
      icon: <Inventory2OutlinedIcon />,
    },
    {
      label: 'Finance',
      value: 'finance',
      icon: <MonetizationOnOutlinedIcon />,
    },
    { label: 'Support', value: 'support', icon: <GroupsIcon /> },
  ];

  const filterCardData = [
    { count: '1', title: 'New Recommended' },
    { count: '12', title: 'Waiting for me' },
    { count: '1', title: 'Rejected' },
    { count: '36', title: 'Completed' },
  ];

  const filterSelectData = [
    { label: 'New Recommended', value: 'new' },
    { label: 'Waiting for me', value: 'waiting' },
    { label: 'Rejected', value: 'rejected' },
    { label: 'Completed', value: 'completed' },
  ];

  const chipBackground = (params: any) => {
    switch (params.value) {
      case 'High':
        return { backgroundColor: red[50], color: red[900], width: '100%' };
      case 'Medium':
        return {
          backgroundColor: yellow[100],
          color: grey[800],
          width: '100%',
        };
      case 'Low':
        return { backgroundColor: blue[50], color: blue[900], width: '100%' };
      default:
        return { backgroundColor: grey[100], color: grey[900], width: '100%' };
    }
  };

  const columns: GridColDef[] = [
    {
      field: 'id',
      headerName: 'ID#',
      flex: 0.5,
      headerAlign: 'center',
      align: 'center',
    },
    {
      field: 'processName',
      headerName: 'Process Name',
      flex: 1,
      headerAlign: 'center',
    },
    { field: 'details', headerName: 'Details', flex: 1, headerAlign: 'center' },
    {
      field: 'lastUpdate',
      headerName: 'Last Update',
      flex: 0.5,
    },
    {
      field: 'priorityLevel',
      headerName: 'Priority Level',
      flex: 1,
      headerAlign: 'center',
      align: 'center',
      renderCell: (params) => (
        <Chip
          label={params.value}
          variant="filled"
          sx={chipBackground(params)}
        />
      ),
    },
    {
      field: 'lastMilestone',
      headerName: 'Last Milestone',
      flex: 1,
      headerAlign: 'center',
      align: 'center',
    },
  ];

  const rows: GridRowsProp = [
    {
      id: '5027',
      processName: 'Request Goods or Services',
      details: '$5k for 5 software licenses',
      lastUpdate: '2 days ago',
      priorityLevel: 'High',
      lastMilestone: 'Budget Approval',
    },
    {
      id: '5028',
      processName: 'Request some other things',
      details: '$50 for some other things',
      lastUpdate: '3 days ago',
      priorityLevel: 'Medium',
      lastMilestone: 'Data Analysis',
    },
    {
      id: '5029',
      processName: 'Request More Things',
      details: '$2k for 2 more things',
      lastUpdate: '4 days ago',
      priorityLevel: 'Low',
      lastMilestone: 'Edit Approval',
    },
    {
      id: '50271',
      processName: 'Request Goods or Services',
      details: '$5k for 5 software licenses',
      lastUpdate: '2 days ago',
      priorityLevel: 'High',
      lastMilestone: 'Budget Approval',
    },
    {
      id: '50281',
      processName: 'Request some other things',
      details: '$50 for some other things',
      lastUpdate: '3 days ago',
      priorityLevel: 'Medium',
      lastMilestone: 'Data Analysis',
    },
    {
      id: '50291',
      processName: 'Request More Things',
      details: '$2k for 2 more things',
      lastUpdate: '4 days ago',
      priorityLevel: 'Low',
      lastMilestone: 'Edit Approval',
    },
    {
      id: '50272',
      processName: 'Request Goods or Services',
      details: '$5k for 5 software licenses',
      lastUpdate: '2 days ago',
      priorityLevel: 'High',
      lastMilestone: 'Budget Approval',
    },
    {
      id: '50282',
      processName: 'Request some other things',
      details: '$50 for some other things',
      lastUpdate: '3 days ago',
      priorityLevel: 'Medium',
      lastMilestone: 'Data Analysis',
    },
    {
      id: '50292',
      processName: 'Request More Things',
      details: '$2k for 2 more things',
      lastUpdate: '4 days ago',
      priorityLevel: 'Low',
      lastMilestone: 'Edit Approval',
    },
    {
      id: '50273',
      processName: 'Request Goods or Services',
      details: '$5k for 5 software licenses',
      lastUpdate: '2 days ago',
      priorityLevel: 'High',
      lastMilestone: 'Budget Approval',
    },
    {
      id: '50283',
      processName: 'Request some other things',
      details: '$50 for some other things',
      lastUpdate: '3 days ago',
      priorityLevel: 'Medium',
      lastMilestone: 'Data Analysis',
    },
    {
      id: '50293',
      processName: 'Request More Things',
      details: '$2k for 2 more things',
      lastUpdate: '4 days ago',
      priorityLevel: 'Low',
      lastMilestone: 'Edit Approval',
    },
  ];

  type TabData = { label: string; value: string; icon: ReactNode };
  const handleTabChange = (tab: TabData) => {
    console.log(tab);
    setSelectedTab(tab.value);
  };

  const handleFilterSelectChange = (event: SelectChangeEvent) => {
    setSelectedFilter(event.target.value);
  };

  useEffect(() => {
    if ('report_metadata' in processInstances) {
      console.log(processInstances.results);
      const mappedColumns = processInstances.report_metadata?.columns.map(
        (column: Record<string, any>) => ({
          field: column.accessor,
          headerName: column.Header,
          flex: 1,
          headerAlign: 'center',
          align: 'center',
        })
      );

      setProcessInstanceColumns(mappedColumns);
    }
  }, [processInstances]);

  return (
    <Grid container spacing={2} xs={12}>
      <Grid item xs={12}>
        <Stack>
          <Toolbar />
          <Box
            sx={{
              display: { xs: 'none', sm: 'block' },
              borderBottom: 1,
              borderColor: 'divider',
            }}
          >
            <Tabs value={selectedTab} variant="fullWidth">
              {tabData.map((tab) => (
                <Tab
                  label={tab.label}
                  value={tab.value}
                  onClick={() => handleTabChange(tab)}
                  icon={tab.icon}
                  iconPosition="start"
                />
              ))}
            </Tabs>
          </Box>

          <Stack direction="row" gap={2} padding={2} sx={{ flexWrap: 'wrap' }}>
            {filterCardData.map((filter) => (
              <FilterCard count={filter.count} title={filter.title} />
            ))}
          </Stack>
          <Stack direction="row" gap={2} padding={2} sx={{ flexWrap: 'wrap' }}>
            <FormControl sx={{ minWidth: 300 }}>
              <InputLabel id="filter-select-label">Filter</InputLabel>
              <Select
                labelId="filter-select-label"
                id="filter-select"
                value={selectedFilter}
                label="Filter"
                onChange={handleFilterSelectChange}
              >
                <MenuItem value="">
                  <ListItemIcon>
                    <FilterAltOutlinedIcon />
                  </ListItemIcon>
                  <ListItemText primary="Filter..." />
                </MenuItem>
                {filterSelectData.map((filter) => (
                  <MenuItem value={filter.value}>
                    <Stack direction="row" gap={2}>
                      <FilterAltOutlinedIcon />
                      {filter.label}
                    </Stack>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Box sx={{ flexGrow: 1 }}>
              <TextField
                fullWidth
                variant="outlined"
                placeholder="Search"
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchOutlinedIcon />
                    </InputAdornment>
                  ),
                }}
              />
            </Box>

            <Stack direction="row" gap={2} padding={2}>
              <FilterAltOutlinedIcon />
              <Columns />
              <Share />
              <Grid />
              <Download />
            </Stack>
          </Stack>

          <DataGrid
            sx={{
              '&, [class^=MuiDataGrid]': { border: 'none' },
            }}
            rows={rows}
            columns={columns}
          />
        </Stack>
      </Grid>
    </Grid>
  );
}
