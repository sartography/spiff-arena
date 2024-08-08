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
  setShowNonActive?: Function;
  showNonActive?: boolean;
  setViewMode?: Function;
  viewMode?: string;
};

function TaskControls({
  showNonActive,
  setShowNonActive,
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
      {setShowNonActive ? (
        <FormControlLabel
          control={
            <Checkbox
              checked={showNonActive}
              onChange={(e) => setShowNonActive(e.target.checked)}
            />
          }
          label="Show non-active"
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
