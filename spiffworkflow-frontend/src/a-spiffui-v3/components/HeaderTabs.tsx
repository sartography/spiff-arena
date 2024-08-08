import React from 'react';
import { Box, Tabs, Tab, Button } from '@mui/material';
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
      <Button
        variant="contained"
        endIcon={<Add />}
        sx={{
          bgcolor: 'background.paper',
          color: 'text.secondary',
          '&:hover': { bgcolor: 'background.default' },
          textTransform: 'none',
          ml: 'auto',
        }}
      >
        Create custom tab
      </Button>
    </Box>
  );
};

export default HeaderTabs;
