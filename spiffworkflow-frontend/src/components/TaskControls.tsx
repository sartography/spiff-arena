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
import { useTranslation } from 'react-i18next';

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
  const { t } = useTranslation();
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
            <MenuItem value="">{t('ungrouped')}</MenuItem>
          ) : (
            <MenuItem value="placeholder" disabled>
              {t('group_by')}
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
          label={t('show_non_active')}
        />
      ) : null}
      {setViewMode ? (
        <SpiffTooltip title={t('toggle_table_tiles')}>
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
