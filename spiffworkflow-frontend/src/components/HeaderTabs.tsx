import React from 'react';
import { Box, Tabs, Tab } from '@mui/material';
import { Add } from '@mui/icons-material';
import { useNavigate } from 'react-router';

const mainBlue = 'primary.main';

type HeaderTabsProps = {
  value: number;
  onChange: (event: React.SyntheticEvent, newValue: number) => void;
};

export default function HeaderTabs({ value, onChange }: HeaderTabsProps) {
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
        sx={{ flexGrow: 1 }} // Make the Tabs container flexible
      >
        <Tab label="Tasks assigned to me" sx={{ textTransform: 'none' }} />
        <Tab label="Workflows created by me" sx={{ textTransform: 'none' }} />
        <Tab
          label={
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <span>Create custom tab</span>
              <Add sx={{ ml: 1 }} />
            </Box>
          }
          sx={{
            ml: 'auto',
            textTransform: 'none',
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
              },
            },
          }}
          onClick={() => navigate('/newui/create-custom-tab')}
        />
      </Tabs>
    </Box>
  );
}
