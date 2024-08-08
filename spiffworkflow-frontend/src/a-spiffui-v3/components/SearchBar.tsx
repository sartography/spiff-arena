import React from 'react';
import { TextField } from '@mui/material';
import { Search } from '@mui/icons-material';

function SearchBar() {
  return (
    <TextField
      placeholder="Search (coming soon)"
      variant="outlined"
      size="small"
      disabled
      InputProps={{
        endAdornment: <Search />,
        sx: { bgcolor: 'background.paper' },
      }}
    />
  );
}

export default SearchBar;
