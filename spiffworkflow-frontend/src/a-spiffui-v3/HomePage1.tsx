import React from 'react';
import {
  Box,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  Checkbox,
  TextField,
  MenuItem,
  IconButton,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';

const data = [
  {
    id: 1,
    type: 'Equipment Purchase',
    description: 'Laptop for Caryn Dolley',
    createdBy: 'Caryn Dolley',
    createdDate: 'Today, 9:56am',
    lastMilestone: 'Pending approval',
    lastUpdated: 'This morning, 9:56am',
  },
  {
    id: 2,
    type: 'Expense Claim',
    description: 'Expense claim for Mark Erasmus',
    createdBy: 'Mark Erasmus',
    createdDate: 'Yesterday, 5:09pm',
    lastMilestone: 'Started',
    lastUpdated: 'Yesterday, 5:09pm',
  },
  {
    id: 3,
    type: 'New Client Onboarding',
    description: 'New client: Andersen Roll Forming LLC',
    createdBy: 'Kerry de Witt',
    createdDate: 'Yesterday, 3:28pm',
    lastMilestone: 'Started',
    lastUpdated: 'Yesterday, 3:28pm',
  },
  {
    id: 4,
    type: 'Equipment Purchase',
    description: 'Additional monitor for Aslan Kenny',
    createdBy: 'Aslan Kenny',
    createdDate: 'Yesterday, 2:46pm',
    lastMilestone: 'Started',
    lastUpdated: 'Yesterday, 2:46pm',
  },
  {
    id: 5,
    type: 'Equipment Purchase',
    description: 'Pedestal and chair for Simon Greeves',
    createdBy: 'Simon Greeves',
    createdDate: '05/16, 10:17am',
    lastMilestone: 'Pending approval',
    lastUpdated: '05/16, 10:17am',
  },
  {
    id: 6,
    type: 'Holiday Request',
    description: 'Holiday request for Caryn Dolley',
    createdBy: 'Caryn Dolley',
    createdDate: '06/12, 15:32pm',
    lastMilestone: 'Pending approval - Budget owner',
    lastUpdated: '06/12, 15:32pm',
  },
];

function TaskTable() {
  return (
    <TableContainer component={Paper}>
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
          {data.map((row) => (
            <TableRow key={row.id}>
              <TableCell>
                <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                  <Typography
                    variant="caption"
                    sx={{
                      backgroundColor: '#E0F7FA',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      display: 'inline-block',
                      marginBottom: '4px',
                    }}
                  >
                    {row.type}
                  </Typography>
                  <Typography variant="body2" color="primary">
                    {row.description}
                  </Typography>
                </Box>
              </TableCell>
              <TableCell>
                {row.createdBy}
                <br />
                {row.createdDate}
              </TableCell>
              <TableCell>{row.lastMilestone}</TableCell>
              <TableCell>{row.lastUpdated}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

function HomePage1() {
  return (
    <Box sx={{ width: '80%', margin: 'auto', mt: 5 }}>
      <Typography variant="h5" gutterBottom>
        Tasks & Processes
      </Typography>
      <Tabs value={0} aria-label="Tasks and Processes Tabs">
        <Tab label="My tasks" />
        <Tab label="My processes" />
        <Tab label="My workflows" />
      </Tabs>
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mt: 3,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <TextField
            variant="outlined"
            size="small"
            placeholder="Search"
            sx={{ mr: 2 }}
            InputProps={{
              endAdornment: (
                <IconButton>
                  <SearchIcon />
                </IconButton>
              ),
            }}
          />
          <TextField
            select
            variant="outlined"
            size="small"
            defaultValue="Group tasks"
            sx={{ width: 150 }}
          >
            <MenuItem value="Group tasks">Group tasks</MenuItem>
            <MenuItem value="Another group">Another group</MenuItem>
          </TextField>
          <Checkbox defaultChecked color="primary" sx={{ ml: 2 }} />
          <Typography>Hide completed</Typography>
        </Box>
        <Typography color="primary" sx={{ cursor: 'pointer' }}>
          Create custom tab
        </Typography>
      </Box>
      <TaskTable />
    </Box>
  );
}

export default HomePage1;
