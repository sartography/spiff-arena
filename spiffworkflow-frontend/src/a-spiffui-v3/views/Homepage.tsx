import React, { useState } from 'react';
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

const mainBlue = 'primary.main';

function Homepage() {
  const [hideCompleted, setHideCompleted] = useState(false);

  const tasks = [
    {
      guid: 'TMPGUID1',
      process_model_display_name: 'Equipment Purchase',
      bpmn_name: 'Authorise purchase order',
      process_instance_summary: 'Laptop for Caryn Dolley',
      created_by: 'Caryn Dolley',
      created_at: 'Today, 9:56am',
      lastMilestone: 'Pending approval',
      lastUpdated: 'This morning, 9:56am',
    },
    {
      guid: 'TMPGUID2',
      process_model_display_name: 'Expense Claim',
      bpmn_name: 'Pre-authorise expense claim',
      process_instance_summary: 'Expense claim for Mark Erasmus',
      created_by: 'Mark Erasmus',
      created_at: 'Yesterday, 5:09pm',
      lastMilestone: 'Started',
      lastUpdated: 'Yesterday, 5:09pm',
    },
    // ... (add more tasks following this structure)
  ];

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
              <TableRow key={task.guid}>
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
                    {task.bpmn_name}
                  </Typography>
                  <Typography variant="body2" color={mainBlue}>
                    {task.process_instance_summary}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" paragraph>
                    {task.created_by}
                  </Typography>
                  <Typography
                    variant="body2"
                    color="textSecondary"
                    sx={{ display: 'flex', alignItems: 'center' }}
                  >
                    <AccessTime sx={{ fontSize: 'small', mr: 0.5 }} />
                    {task.created_at}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography
                    variant="body2"
                    sx={{ display: 'flex', alignItems: 'center' }}
                  >
                    {task.lastMilestone === 'Pending approval' ? '◯' : '●'}{' '}
                    {task.lastMilestone}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography
                    variant="body2"
                    color="textSecondary"
                    sx={{ display: 'flex', alignItems: 'center' }}
                  >
                    <AccessTime sx={{ fontSize: 'small', mr: 0.5 }} />
                    {task.lastUpdated}
                  </Typography>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}

export default Homepage;
