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
import { green } from '@carbon/colors';
import Columns from '../../assets/icons/columns-2.svg';
import Share from '../../assets/icons/share-arrow.svg';
import Download from '../../assets/icons/download.svg';
import Toolbar from './Toolbar';
import FilterCard from './FilterCard';
import useProcessInstances from '../../hooks/useProcessInstances';
import ProcessInstanceCard from './ProcessInstanceCard';

export default function Dashboards() {
  const [selectedTab, setSelectedTab] = useState('myProcesses');
  const [selectedFilter, setSelectedFilter] = useState('new');
  // TODO: Type of this doesn't seem to be ProcessInstance
  // Find out and remove "any""
  const [processInstanceColumns, setProcessInstanceColumns] = useState<
    GridColDef[]
  >([]);
  const [processInstanceRows, setProcessInstanceRows] = useState<
    GridRowsProp[]
  >([]);

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
      case 'Completed':
        return { backgroundColor: blue[50], color: blue[900], width: '100%' };
      case 'Started':
        return { backgroundColor: green[10], color: green[90], width: '100%' };
      default:
        return { backgroundColor: grey[100], color: grey[900], width: '100%' };
    }
  };

  type TabData = { label: string; value: string; icon: ReactNode };
  const handleTabChange = (tab: TabData) => {
    setSelectedTab(tab.value);
  };

  const handleFilterSelectChange = (event: SelectChangeEvent) => {
    setSelectedFilter(event.target.value);
  };

  useEffect(() => {
    if ('report_metadata' in processInstances) {
      const mappedColumns = processInstances.report_metadata?.columns.map(
        (column: Record<string, any>) => ({
          field: column.accessor,
          headerName: column.Header,
          flex: (() => {
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
            column.Header === 'Last milestone'
              ? (params: Record<string, any>) => (
                  <Chip
                    label={params.value}
                    variant="filled"
                    sx={chipBackground(params)}
                  />
                )
              : null,
        })
      );

      setProcessInstanceColumns(mappedColumns);
      setProcessInstanceRows(processInstances.results);
    }
  }, [processInstances]);

  return (
    <Grid container spacing={2}>
      <Grid item>
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
                sx={{ width: { xs: 300, sm: '100%' } }}
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

          <Box sx={{ display: { xs: 'none', lg: 'block' } }}>
            <DataGrid
              sx={{
                '&, [class^=MuiDataGrid]': { border: 'none' },
              }}
              rows={processInstanceRows}
              columns={processInstanceColumns}
            />
          </Box>
          <Box sx={{ display: { xs: 'block', lg: 'none' } }}>
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
        </Stack>
      </Grid>
    </Grid>
  );
}
