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
  Slide,
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
import Columns from '../../assets/icons/columns-2.svg';
import Share from '../../assets/icons/share-arrow.svg';
import Download from '../../assets/icons/download.svg';
import Toolbar from './Toolbar';
import FilterCard from './FilterCard';
import useProcessInstances from '../../hooks/useProcessInstances';
import ProcessInstanceCard from './ProcessInstanceCard';
import InfoWindow from './InfoWindow';
/**
 * This "Dashboards" view is the home view for the new Spiff UI.
 */
export default function Dashboards() {
  const [selectedTab, setSelectedTab] = useState('myProcesses');
  const [selectedFilter, setSelectedFilter] = useState('new');
  const [infoPanelOpen, setInfoPanelIsOpen] = useState(false);
  // TODO: Type of this doesn't seem to be ProcessInstance
  // Find out and remove "any""
  const [processInstanceColumns, setProcessInstanceColumns] = useState<
    GridColDef[]
  >([]);
  const [processInstanceRows, setProcessInstanceRows] = useState<
    GridRowsProp[]
  >([]);
  const [selectedGridRow, setSelectedGridRow] = useState<Record<string, any>>(
    {}
  );

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

  type TabData = { label: string; value: string; icon: ReactNode };
  const handleTabChange = (tab: TabData) => {
    setSelectedTab(tab.value);
  };

  const handleFilterSelectChange = (event: SelectChangeEvent) => {
    setSelectedFilter(event.target.value);
  };

  const handleSearchChange = (search: string) => {
    const filtered = search
      ? processInstances.results.filter((instance: any) => {
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
              .includes(search.toLowerCase())
          );
        })
      : processInstances.results;

    setProcessInstanceRows(filtered);
  };

  const handleGridRowClick = (data: Record<string, any>) => {
    setSelectedGridRow(data);
    setInfoPanelIsOpen((curr) => !curr);
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
      setProcessInstanceRows([...processInstances.results]);
    }
  }, [processInstances]);

  return (
    <>
      <Grid container spacing={2} width="100%">
        <Grid item sx={{ width: '100%' }}>
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

            <Stack
              direction="row"
              gap={2}
              padding={2}
              sx={{ flexWrap: 'wrap' }}
            >
              {filterCardData.map((filter) => (
                <FilterCard count={filter.count} title={filter.title} />
              ))}
            </Stack>
            <Stack
              direction="row"
              gap={2}
              padding={2}
              sx={{ flexWrap: 'wrap' }}
            >
              <FormControl>
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
                  onChange={(e) => handleSearchChange(e.target.value)}
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
          </Stack>
        </Grid>
      </Grid>

      {/** Absolutely positioned info window */}
      {!Object.keys(selectedGridRow).length && (
        <Slide in direction="left" mountOnEnter unmountOnExit>
          <Stack
            sx={{
              display: { xs: 'none', md: 'block' },
              position: 'fixed',
              right: 0,
              top: 0,
              width: '40%',
              height: '100%',
              padding: 1,
              alignContent: 'center',
            }}
          >
            <Box sx={{ width: '100%', height: '70%' }}>
              <InfoWindow data={selectedGridRow} />
            </Box>
          </Stack>
        </Slide>
      )}
    </>
  );
}
