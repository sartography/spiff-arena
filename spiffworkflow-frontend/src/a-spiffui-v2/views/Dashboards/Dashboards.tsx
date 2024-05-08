import {
  Box,
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
import { ReactNode, useState } from 'react';
import Inventory2OutlinedIcon from '@mui/icons-material/Inventory2Outlined';
import MonetizationOnOutlinedIcon from '@mui/icons-material/MonetizationOnOutlined';
import GroupsIcon from '@mui/icons-material/Groups';
import AssignmentOutlinedIcon from '@mui/icons-material/AssignmentOutlined';
import FilterAltOutlinedIcon from '@mui/icons-material/FilterAltOutlined';
import SearchOutlinedIcon from '@mui/icons-material/SearchOutlined';
import Columns from '../../assets/icons/columns-2.svg';
import Share from '../../assets/icons/share-arrow.svg';
import Download from '../../assets/icons/download.svg';
import Toolbar from './Toolbar';
import FilterCard from './FilterCard';
import InfoWindow from './InfoWindow';
import MyProcesses from './MyProcesses';
import MyTasks from './MyTasks';
/**
 * This "Dashboards" view is the home view for the new Spiff UI.
 */
export default function Dashboards() {
  const [selectedTab, setSelectedTab] = useState('myProcesses');
  const [selectedFilter, setSelectedFilter] = useState('new');
  const [searchText, setSearchText] = useState('');
  const [panelData, setPanelData] = useState<Record<string, any>>({});
  const [infoPanelOpen, setInfoPanelIsOpen] = useState(false);

  const tabData = [
    {
      label: 'My Processes',
      value: 'myProcesses',
      icon: <Inventory2OutlinedIcon />,
    },
    {
      label: 'My Tasks',
      value: 'myTasks',
      icon: <MonetizationOnOutlinedIcon />,
    },
    {
      label: 'Finance',
      value: 'finance',
      icon: <AssignmentOutlinedIcon />,
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

  type TabData = { label: string; value: string; icon: ReactNode };
  const handleTabChange = (tab: TabData) => {
    setSelectedTab(tab.value);
  };

  const handleFilterSelectChange = (event: SelectChangeEvent) => {
    setSelectedFilter(event.target.value);
  };

  const handleSearchChange = (search: string) => {
    setSearchText(search);
  };

  const handleRowSelect = (data: Record<string, any>) => {
    setPanelData(data);
    setInfoPanelIsOpen(true);
  };

  const handleInfoWindowClose = () => {
    setInfoPanelIsOpen(false);
  };

  const displayGrid = () => {
    if (selectedTab === 'myTasks') {
      return <MyTasks filter={searchText} callback={handleRowSelect} />;
    }
    return <MyProcesses filter={searchText} callback={handleRowSelect} />;
  };

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
            {displayGrid()}
          </Stack>
        </Grid>
      </Grid>

      {/** Absolutely positioned info window */}
      {Object.keys(panelData).length && (
        <Slide in={infoPanelOpen} direction="left" mountOnEnter unmountOnExit>
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
              <InfoWindow data={panelData} callback={handleInfoWindowClose} />
            </Box>
          </Stack>
        </Slide>
      )}
    </>
  );
}
