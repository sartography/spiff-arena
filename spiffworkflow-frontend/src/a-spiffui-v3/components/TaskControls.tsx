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
import SpiffTooltip from '../../components/SpiffTooltip';

type OwnProps = {
  onUserGroupSelect?: Function;
  setShowNonActive?: Function;
  setViewMode?: Function;
  showNonActive?: boolean;
  userGroups?: string[];
  viewMode?: string;
};

function TaskControls({
  onUserGroupSelect,
  setShowNonActive,
  setViewMode,
  showNonActive,
  userGroups,
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
        <SpiffTooltip title="Toggle table / tiles">
          <IconButton
            onClick={() => setViewMode(viewMode === 'table' ? 'tile' : 'table')}
          >
            <ViewModule />
          </IconButton>
        </SpiffTooltip>
      ) : null}
    </Box>
  );
}

export default TaskControls;
