import React from 'react';
import {
  Box,
  Select,
  MenuItem,
  Checkbox,
  IconButton,
  FormControlLabel,
} from '@mui/material';
import { ViewModule } from '@mui/icons-material';
import SpiffTooltip from './SpiffTooltip';

type OwnProps = {
  onGroupBySelect?: Function;
  setShowNonActive?: Function;
  setViewMode?: Function;
  showNonActive?: boolean;
  groupByOptions?: string[] | null;
  viewMode?: string;
  selectedGroupBy?: string | null;
};

function TaskControls({
  onGroupBySelect,
  setShowNonActive,
  setViewMode,
  showNonActive,
  groupByOptions,
  viewMode = 'table',
  selectedGroupBy,
}: OwnProps) {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center' }}>
      {onGroupBySelect ? (
        <Select
          value={selectedGroupBy || 'placeholder'}
          size="small"
          onChange={(e) => {
            onGroupBySelect(e.target.value);
          }}
          sx={{ mr: 2, bgcolor: 'background.paper' }}
        >
          {selectedGroupBy ? (
            <MenuItem value="">Ungrouped</MenuItem>
          ) : (
            <MenuItem value="placeholder" disabled>
              Group by
            </MenuItem>
          )}
          {groupByOptions?.map((group) => (
            <MenuItem key={group} value={group}>
              {group}
            </MenuItem>
          ))}
        </Select>
      ) : null}
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
