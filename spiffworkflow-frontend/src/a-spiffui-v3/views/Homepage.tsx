import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Tabs,
  Tab,
  TextField,
  Select,
  MenuItem,
  Checkbox,
  FormControlLabel,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Button,
  Chip,
} from '@mui/material';
import { Search, ViewModule, Add, AccessTime } from '@mui/icons-material';
import HttpService from '../../services/HttpService';
import DateAndTimeService from '../../services/DateAndTimeService';
import { ProcessInstanceTask } from '../../interfaces';

const mainBlue = 'primary.main';

function Homepage() {
  const [hideCompleted, setHideCompleted] = useState(false);
  const [tasks, setTasks] = useState<ProcessInstanceTask[] | null>(null);

  useEffect(() => {
    const getTasks = () => {
      const setTasksFromResult = (result: any) => {
        setTasks(result.results);
      };
      HttpService.makeCallToBackend({
        path: '/tasks',
        successCallback: setTasksFromResult,
      });
    };
    getTasks();
  }, []);

  const taskTable = () => {
    if (tasks === null) {
      return null;
    }

    return (
      <TableContainer component={Paper} sx={{ boxShadow: 'none' }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Task details</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Last milestone</TableCell>
              <TableCell>Last updated</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {tasks.map((task) => (
              <TableRow key={task.id}>
                <TableCell>
                  <Chip
                    label={task.process_model_display_name}
                    size="small"
                    sx={{
                      bgcolor: '#E0E0E0',
                      color: '#616161',
                      mb: 1,
                      fontWeight: 'normal',
                    }}
                  />
                  <Typography variant="body2" paragraph>
                    {task.task_name || task.task_title}
                  </Typography>
                  <Typography variant="body2" color={mainBlue}>
                    {task.process_instance_summary}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" paragraph>
                    {task.process_initiator_username}
                  </Typography>
                  <Typography
                    variant="body2"
                    color="textSecondary"
                    sx={{ display: 'flex', alignItems: 'center' }}
                  >
                    <AccessTime sx={{ fontSize: 'small', mr: 0.5 }} />
                    {DateAndTimeService.convertSecondsToFormattedDateTime(
                      task.created_at_in_seconds,
                    )}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography
                    variant="body2"
                    sx={{ display: 'flex', alignItems: 'center' }}
                  >
                    {'● '}
                    {task.last_milestone_bpmn_name}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography
                    variant="body2"
                    color="textSecondary"
                    sx={{ display: 'flex', alignItems: 'center' }}
                  >
                    <AccessTime sx={{ fontSize: 'small', mr: 0.5 }} />
                    {DateAndTimeService.convertSecondsToFormattedDateTime(
                      task.created_at_in_seconds,
                    )}
                  </Typography>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  return (
    <Box
      component="main"
      sx={{
        flexGrow: 1,
        p: 3,
        overflow: 'auto',
        height: '100vh',
      }}
    >
      <Typography variant="h5" sx={{ mb: 2 }}>
        Tasks & Processes
      </Typography>
      <Box
        sx={{
          mb: 2,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <Tabs value={0}>
          <Tab label="Tasks assigned to me" sx={{ textTransform: 'none' }} />
          <Tab label="Workflows created by me" sx={{ textTransform: 'none' }} />
        </Tabs>
        <Button
          variant="contained"
          startIcon={<Add />}
          sx={{
            bgcolor: mainBlue,
            '&:hover': { bgcolor: mainBlue },
            textTransform: 'none',
            ml: 'auto',
          }}
        >
          Create custom tab
        </Button>
      </Box>
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 2,
        }}
      >
        <TextField
          placeholder="Search"
          variant="outlined"
          size="small"
          InputProps={{
            endAdornment: <Search />,
            sx: { bgcolor: 'background.paper' },
          }}
        />
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Select
            value="Group tasks"
            size="small"
            sx={{ mr: 2, bgcolor: 'background.paper' }}
          >
            <MenuItem value="Group tasks">Group tasks</MenuItem>
          </Select>
          <FormControlLabel
            control={
              <Checkbox
                checked={hideCompleted}
                onChange={(e) => setHideCompleted(e.target.checked)}
              />
            }
            label="Hide completed"
          />
          <IconButton>
            <ViewModule />
          </IconButton>
        </Box>
      </Box>
      {taskTable()}
    </Box>
  );
}

export default Homepage;
