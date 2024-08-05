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
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Button,
  Tooltip,
} from '@mui/material';
import {
  Search,
  ViewModule,
  Home,
  Assignment,
  Add,
  AccessTime,
  Person,
  ChevronLeft,
  ChevronRight,
} from '@mui/icons-material';

const drawerWidth = 240;
const collapsedDrawerWidth = 64;
const mainBlue = '#00A3E0'; // Spiffworkflow blue color

function SideNav({ selectedTab, onSelectTab, isCollapsed, onToggleCollapse }) {
  return (
    <Box
      sx={{
        width: isCollapsed ? collapsedDrawerWidth : drawerWidth,
        flexShrink: 0,
        borderRight: '1px solid #e0e0e0',
        height: '100vh',
        bgcolor: 'white',
        transition: 'width 0.3s',
        overflow: 'hidden',
        position: 'relative',
      }}
    >
      <Box
        sx={{
          p: 2,
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        {!isCollapsed && (
          <Typography
            variant="h6"
            color={mainBlue}
            sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center' }}
          >
            <Assignment sx={{ mr: 1 }} />
            Spiffworkflow
          </Typography>
        )}
        <IconButton
          onClick={onToggleCollapse}
          sx={{ ml: isCollapsed ? 'auto' : 0 }}
        >
          {isCollapsed ? <ChevronRight /> : <ChevronLeft />}
        </IconButton>
      </Box>
      <List>
        {[
          { text: 'HOME', icon: <Home /> },
          { text: 'TASKS & PROCESSES', icon: <Assignment /> },
          { text: 'START NEW PROCESS', icon: <Add /> },
        ].map((item, index) => (
          <ListItem
            button
            key={item.text}
            onClick={() => onSelectTab(index)}
            sx={{
              bgcolor: selectedTab === index ? '#F0F9FF' : 'inherit',
              color: selectedTab === index ? mainBlue : 'inherit',
              borderLeft:
                selectedTab === index
                  ? `4px solid ${mainBlue}`
                  : '4px solid transparent',
              '&:hover': {
                bgcolor: '#F0F9FF',
              },
              justifyContent: isCollapsed ? 'center' : 'flex-start',
            }}
          >
            <Tooltip title={isCollapsed ? item.text : ''} placement="right">
              <ListItemIcon
                sx={{ color: 'inherit', minWidth: isCollapsed ? 24 : 40 }}
              >
                {item.icon}
              </ListItemIcon>
            </Tooltip>
            {!isCollapsed && (
              <ListItemText
                primary={item.text}
                primaryTypographyProps={{
                  fontSize: '0.875rem',
                  fontWeight: selectedTab === index ? 'bold' : 'normal',
                }}
              />
            )}
          </ListItem>
        ))}
      </List>
      <Box
        sx={{
          position: 'absolute',
          bottom: 16,
          left: isCollapsed ? '50%' : 16,
          transform: isCollapsed ? 'translateX(-50%)' : 'none',
        }}
      >
        <IconButton>
          <Person />
        </IconButton>
      </Box>
    </Box>
  );
}

function TasksProcesses() {
  const [selectedTab, setSelectedTab] = useState(1);
  const [hideCompleted, setHideCompleted] = useState(false);
  const [isNavCollapsed, setIsNavCollapsed] = useState(false);

  const toggleNavCollapse = () => {
    setIsNavCollapsed(!isNavCollapsed);
  };

  const tasks = [
    {
      category: 'Equipment Purchase',
      details: 'Authorise purchase order\nLaptop for Caryn Dolley',
      created: 'Caryn Dolley\nToday, 9:56am',
      lastMilestone: 'Pending approval',
      lastUpdated: 'This morning, 9:56am',
    },
    {
      category: 'Expense Claim',
      details: 'Pre-authorise expense claim\nExpense claim for Mark Erasmus',
      created: 'Mark Erasmus\nYesterday, 5:09pm',
      lastMilestone: 'Started',
      lastUpdated: 'Yesterday, 5:09pm',
    },
    // ... other tasks ...
  ];

  return (
    <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      <SideNav
        selectedTab={selectedTab}
        onSelectTab={setSelectedTab}
        isCollapsed={isNavCollapsed}
        onToggleCollapse={toggleNavCollapse}
      />
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          overflow: 'auto',
          bgcolor: '#F9FAFB',
        }}
      >
        <Typography variant="h5" sx={{ mb: 2 }}>
          Tasks & Processes
        </Typography>
        <Box sx={{ mb: 2 }}>
          <Tabs value={0}>
            <Tab label="My tasks" sx={{ textTransform: 'none' }} />
            <Tab label="My processes" sx={{ textTransform: 'none' }} />
            <Tab label="My workflows" sx={{ textTransform: 'none' }} />
          </Tabs>
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
              sx: { bgcolor: 'white' },
            }}
          />
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Select
              value="Group tasks"
              size="small"
              sx={{ mr: 2, bgcolor: 'white' }}
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
              {tasks.map((task, index) => (
                <TableRow key={index}>
                  <TableCell>
                    <Typography variant="body2" color="textSecondary">
                      {task.category}
                    </Typography>
                    <Typography variant="body2" paragraph>
                      {task.details.split('\n')[0]}
                    </Typography>
                    <Typography variant="body2" color={mainBlue}>
                      {task.details.split('\n')[1]}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" paragraph>
                      {task.created.split('\n')[0]}
                    </Typography>
                    <Typography
                      variant="body2"
                      color="textSecondary"
                      sx={{ display: 'flex', alignItems: 'center' }}
                    >
                      <AccessTime sx={{ fontSize: 'small', mr: 0.5 }} />
                      {task.created.split('\n')[1]}
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
        <Box sx={{ position: 'absolute', top: 16, right: 16 }}>
          <Button
            variant="contained"
            startIcon={<Add />}
            sx={{
              bgcolor: mainBlue,
              '&:hover': { bgcolor: mainBlue },
              textTransform: 'none',
            }}
          >
            Create custom tab
          </Button>
        </Box>
      </Box>
    </Box>
  );
}

export default TasksProcesses;
