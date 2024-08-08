import React from 'react';
import { Box, Select, MenuItem, FormControlLabel, Checkbox, IconButton } from '@mui/material';
import { ViewModule } from '@mui/icons-material';

const TaskControls = ({ hideCompleted, setHideCompleted }) => (
  <Box sx={{ display: 'flex', alignItems: 'center' }}>
    <Select value="Group tasks" size="small" sx={{ mr: 2, bgcolor: 'background.paper' }}>
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
);

export default TaskControls;
