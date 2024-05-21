import {
  Box,
  Container,
  FormControl,
  Grid,
  InputAdornment,
  InputLabel,
  ListItemIcon,
  ListItemText,
  MenuItem,
  Paper,
  Select,
  SelectChangeEvent,
  Slide,
  Stack,
  TextField,
  useTheme,
} from '@mui/material';
import { useEffect, useState } from 'react';
import FilterAltOutlinedIcon from '@mui/icons-material/FilterAltOutlined';
import SearchOutlinedIcon from '@mui/icons-material/SearchOutlined';
import Columns from '../../assets/icons/columns-2.svg';
import Share from '../../assets/icons/share-arrow.svg';
import Download from '../../assets/icons/download.svg';
import MyProcesses from './myProcesses/MyProcesses';
import InfoPanel from '../../components/InfoPanel';
import MyTasks from './myTasks/MyTasks';
import DashboardCharts from './DashboardCharts';
import useProcessInstanceCollection from '../../hooks/useProcessInstanceCollection';
import useProcessInstanceTimes from '../../hooks/useProcessInstanceTimes';
import useTaskCollection from '../../hooks/useTaskCollection';
/**
 * This "Dashboards" view is the home view for the new Spiff UI.
 */
export default function Dashboards() {
  const [selectedFilter, setSelectedFilter] = useState('new');
  const [searchText, setSearchText] = useState('');
  const [panelData, setPanelData] = useState<Record<string, any>>({});
  const [infoPanelOpen, setInfoPanelIsOpen] = useState(false);
  const { processInstanceCollection } = useProcessInstanceCollection();
  const { taskCollection } = useTaskCollection({ processInfo: {} });
  const { processInstanceTimesReport, setProcessInstances } =
    useProcessInstanceTimes();

  const isDark = useTheme().palette.mode === 'dark';

  const filterSelectData = [
    { label: 'My Processes', value: 'myProcesses' },
    { label: 'Finance', value: 'finance' },
    { label: 'Support', value: 'support' },
  ];

  const handleFilterSelectChange = (event: SelectChangeEvent) => {
    setSelectedFilter(event.target.value);
  };

  const handleSearchChange = (search: string) => {
    setSearchText(search);
  };

  const handleRowSelect = (data: Record<string, any>) => {
    if (data !== panelData) {
      setPanelData(data);
      setInfoPanelIsOpen(true);
    } else {
      setInfoPanelIsOpen(!infoPanelOpen);
    }
  };

  const handleInfoWindowClose = () => {
    setInfoPanelIsOpen(false);
  };

  const loadInfoPanel = () => {
    // if (selectedTab === 'myTasks') {
    //   return <TaskInfo data={panelData} />;
    // }
    return <Box />; // <ProcessInfo data={panelData} />;
  };

  useEffect(() => {
    if (Object.keys(processInstanceCollection).length) {
      setProcessInstances(processInstanceCollection.results);
    }
  }, [processInstanceCollection]);

  return (
    <>
      <Grid container spacing={2} sx={{ width: '100%' }}>
        <Grid item sx={{ width: '100%' }}>
          {/**
           * We have to force padding in MuiContainer to 0px
           * to meet design requirement
           */}
          <Container
            sx={{
              padding: '0px !important',
              backgroundColor: 'background.bluegreylight',
            }}
          >
            <Stack sx={{ margin: 0, padding: 0 }}>
              <Box
                sx={{
                  border: 1,
                  borderColor: 'divider',
                  padding: 4,
                }}
              >
                <DashboardCharts times={processInstanceTimesReport} />
              </Box>
              <Paper
                elevation={0}
                sx={{
                  display: 'flex',
                  gap: 2,
                  flexWrap: 'wrap',
                  padding: 2,
                  borderColor: 'divider',
                  backgroundColor: isDark
                    ? 'background.paper'
                    : 'background.bluegreymedium',
                }}
              >
                <FormControl>
                  <InputLabel id="filter-select-label">Filter</InputLabel>
                  <Select
                    labelId="filter-select-label"
                    id="filter-select"
                    value={selectedFilter}
                    label="Filter"
                    onChange={handleFilterSelectChange}
                    sx={{
                      backgroundColor: isDark
                        ? 'background.offblack'
                        : 'background.medium',
                    }}
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
                    sx={{
                      width: {
                        xs: 300,
                        sm: '100%',
                      },
                      backgroundColor: isDark
                        ? 'background.offblack'
                        : 'background.medium',
                    }}
                    variant="outlined"
                    placeholder="Search"
                    value={searchText}
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
                  <Columns />
                  <Share />
                  <Grid />
                  <Download />
                </Stack>
              </Paper>
              <Paper>
                <Stack direction="row" sx={{ flex: 1 }}>
                  <MyProcesses
                    filter={searchText}
                    callback={handleRowSelect}
                    pis={processInstanceCollection}
                  />
                  <MyTasks
                    filter={searchText}
                    callback={handleRowSelect}
                    tasks={taskCollection}
                  />
                </Stack>
              </Paper>
            </Stack>
          </Container>
        </Grid>
      </Grid>
      {/** Absolutely positioned info window */}
      {Object.keys(panelData).length ? (
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
              <InfoPanel
                title={panelData.process_model_display_name || ''}
                callback={handleInfoWindowClose}
              >
                {loadInfoPanel() || <Box />}
              </InfoPanel>
            </Box>
          </Stack>
        </Slide>
      ) : null}
    </>
  );
}
