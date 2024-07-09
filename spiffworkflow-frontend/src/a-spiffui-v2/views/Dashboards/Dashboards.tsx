import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
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
  Typography,
  useTheme,
} from '@mui/material';
import { SyntheticEvent, useEffect, useState } from 'react';
import FilterAltOutlinedIcon from '@mui/icons-material/FilterAltOutlined';
import SearchOutlinedIcon from '@mui/icons-material/SearchOutlined';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import Columns from '../../assets/icons/columns-2.svg';
import Share from '../../assets/icons/share-arrow.svg';
import Download from '../../assets/icons/download.svg';
import MyProcesses from './myProcesses/MyProcesses';
import InfoPanel from '../../components/InfoPanel';
import DashboardCharts from './DashboardCharts';
import useProcessInstanceCollection from '../../hooks/useProcessInstanceCollection';
import useProcessInstanceTimes from '../../hooks/useProcessInstanceTimes';
import TaskInfo from './infopanels/TaskInfo';
import ProcessInfo from './infopanels/ProcessInfo';

/**
 * This "Dashboards" view is the home view for the new Spiff UI.
 */
export default function Dashboards() {
  const [selectedFilter, setSelectedFilter] = useState('myProcesses');
  const [searchText, setSearchText] = useState('');
  const [panelData, setPanelData] = useState<Record<string, any>>({});
  const [dashboardAccordionOpen, setDashboardAccordionOpen] = useState(true);
  const [infoPanelOpen, setInfoPanelIsOpen] = useState(false);
  const [isTaskData, setIsTaskData] = useState(false);
  const { processInstanceCollection } = useProcessInstanceCollection();
  const { processInstanceTimesReport, setProcessInstances } =
    useProcessInstanceTimes();

  const isDark = useTheme().palette.mode === 'dark';
  const bgPaper = 'background.paper';

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

  const handleProcessRowSelect = (data: Record<string, any>) => {
    setIsTaskData(false);
    if (data !== panelData) {
      setPanelData(data);
      setInfoPanelIsOpen(true);
    } else {
      setInfoPanelIsOpen(!infoPanelOpen);
    }
  };

  const handleTaskRowSelect = (data: Record<string, any>) => {
    setIsTaskData(true);
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

  const handleAccordionChange = (event: SyntheticEvent, expanded: boolean) => {
    setDashboardAccordionOpen(expanded);
  };

  useEffect(() => {
    if (Object.keys(processInstanceCollection).length) {
      setProcessInstances(processInstanceCollection.results);
    }
    // ignore this because it doesn't realize that setProcessInstances is a state
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [processInstanceCollection]);

  return (
    <>
      <Grid container spacing={2}>
        <Grid item sx={{ width: '100%' }}>
          {/**
           * We have to force padding in MuiContainer to 0px
           * to meet design requirement
           */}
          <Container
            maxWidth={false}
            sx={{
              padding: '0px !important',
              backgroundColor: 'background.light',
            }}
          >
            <Stack sx={{ margin: 0, padding: 0 }}>
              <Box
                sx={{
                  border: 1,
                  borderColor: 'divider',
                }}
              >
                <Accordion
                  defaultExpanded
                  sx={{ boxShadow: 'none', padding: 2 }}
                  onChange={handleAccordionChange}
                >
                  <AccordionSummary
                    expandIcon={<ExpandMoreIcon />}
                    aria-controls="panel1-content"
                    id="panel1-header"
                  >
                    <Typography color="primary">Dashboard KPIs</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <DashboardCharts times={processInstanceTimesReport} />
                  </AccordionDetails>
                </Accordion>
              </Box>
              <Paper
                elevation={0}
                sx={{
                  display: 'flex',
                  gap: 2,
                  flexWrap: 'wrap',
                  padding: 2,
                  borderColor: 'divider',
                  borderRadius: 0,
                  backgroundColor: isDark
                    ? bgPaper
                    : 'rgba(176, 190, 197, 0.3)',
                }}
              >
                <FormControl>
                  <InputLabel
                    id="filter-select-label"
                    sx={{ display: { xs: 'none', md: 'block' } }}
                  >
                    Filter
                  </InputLabel>
                  <Select
                    labelId="filter-select-label"
                    id="filter-select"
                    value={selectedFilter}
                    label="Filter"
                    onChange={handleFilterSelectChange}
                    sx={{
                      minWidth: 200,
                      backgroundColor: bgPaper,
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
                      backgroundColor: bgPaper,
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

                <Stack direction="row" gap={2} sx={{ padding: 2 }}>
                  <Columns />
                  <Share />
                  <Grid />
                  <Download />
                </Stack>
              </Paper>
              <Paper>
                <Stack
                  direction="row"
                  sx={{
                    flex: 1,
                    height: dashboardAccordionOpen
                      ? 'calc(100vh - 500px)'
                      : 'calc(100vh - 245px)',
                  }}
                >
                  <Box sx={{ width: '100%' }}>
                    <MyProcesses
                      filter={searchText}
                      callback={handleProcessRowSelect}
                      pis={processInstanceCollection}
                    />
                  </Box>
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
              display: { xs: 'none', sm: 'block' },
              position: 'fixed',
              right: -20,
              top: 0,
              width: '50%',
              height: '100%',
              minWidth: 700,
              padding: 1,
              alignContent: 'center',
            }}
          >
            <Box sx={{ width: '100%', height: '70%' }}>
              <InfoPanel callback={handleInfoWindowClose}>
                {isTaskData ? (
                  <TaskInfo data={panelData} />
                ) : (
                  <ProcessInfo
                    pi={panelData}
                    callback={handleTaskRowSelect}
                    filter={searchText}
                  />
                )}
              </InfoPanel>
            </Box>
          </Stack>
        </Slide>
      ) : null}
    </>
  );
}
