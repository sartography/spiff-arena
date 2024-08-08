import React from 'react';
import { Box, Tabs, Tab } from '@mui/material';
import { Add } from '@mui/icons-material';
import { useNavigate } from 'react-router';

const mainBlue = 'primary.main';

interface HeaderTabsProps {
  value: number;
  onChange: (event: React.SyntheticEvent, newValue: number) => void;
}

const HeaderTabs: React.FC<HeaderTabsProps> = ({ value, onChange }) => {
  const navigate = useNavigate();

  return (
    <Box
      sx={{
        mb: 2,
        display: 'flex',
        justifyContent: 'space-between',
        borderWidth: '2px',
        borderBottomStyle: 'solid',
        borderColor: 'borders.table',
        alignItems: 'center',
      }}
    >
      <Tabs
        value={value}
        TabIndicatorProps={{
          style: { height: 3 },
        }}
        onChange={onChange}
      >
        <Tab label="Tasks assigned to me" sx={{ textTransform: 'none' }} />
        <Tab label="Workflows created by me" sx={{ textTransform: 'none' }} />
      </Tabs>
      <Tab
        label={
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <span>Create custom tab</span>
            <Add sx={{ ml: 1 }} />
          </Box>
        }
        sx={{ 
          textTransform: 'none', 
          ml: 'auto', 
          color: mainBlue,
          '& .MuiBox-root': {
            display: 'flex', 
            alignItems: 'center',
            '& .MuiSvgIcon-root': {
              ml: 1,
              bgcolor: mainBlue,
              color: 'white',
              borderRadius: '50%',
              padding: '2px',
            }
          }
        }}
        onClick={() => navigate('/create-custom-tab')}
      />
    </Box>
  );
};

export default HeaderTabs;
