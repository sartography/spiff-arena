import React from 'react';
import {
  Box,
  Select,
  MenuItem,
  FormControlLabel,
  Checkbox,
  IconButton,
} from '@mui/material';
import { ViewModule } from '@mui/icons-material';

type OwnProps = {
  setHideCompleted?: Function;
  hideCompleted?: boolean;
  setViewMode?: Function;
  viewMode?: string;
};

function TaskControls({
  hideCompleted,
  setHideCompleted,
  setViewMode,
  viewMode = 'table',
}: OwnProps) {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center' }}>
      <Select
        value="Group tasks"
        size="small"
        sx={{ mr: 2, bgcolor: 'background.paper' }}
      >
        <MenuItem value="Group tasks">Group tasks</MenuItem>
      </Select>
      {setHideCompleted ? (
        <FormControlLabel
          control={
            <Checkbox
              checked={hideCompleted}
              onChange={(e) => setHideCompleted(e.target.checked)}
            />
          }
          label="Hide completed"
        />
      ) : null}
      {setViewMode ? (
        <IconButton
          onClick={() => setViewMode(viewMode === 'table' ? 'tile' : 'table')}
        >
          <ViewModule />
        </IconButton>
      ) : null}
    </Box>
  );
}

export default TaskControls;
