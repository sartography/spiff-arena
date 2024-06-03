import { Box, InputAdornment, Paper, TextField } from '@mui/material';
import { useState } from 'react';
import SearchOutlinedIcon from '@mui/icons-material/SearchOutlined';

export default function SearchBar() {
  const [searchText, setSearchText] = useState('');
  const bgPaper = 'background.paper';

  const handleSearchChange = (search: string) => {
    setSearchText(search);
  };

  return (
    <Paper
      elevation={0}
      sx={{
        width: '100%',
        maxWidth: 1200,
        display: 'flex',
        gap: 2,
        flexWrap: 'wrap',
        padding: 2,
        borderColor: `borders.primary`,
        borderWidth: 1,
        borderStyle: 'solid',
      }}
    >
      <Box sx={{ flexGrow: 1 }}>
        <TextField
          size="small"
          sx={{
            width: {
              xs: 300,
              sm: '100%',
            },
            backgroundColor: bgPaper,
          }}
          variant="outlined"
          placeholder="Search"
          value={searchText}
          onChange={(e) => handleSearchChange(e.target.value)}
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <SearchOutlinedIcon />
              </InputAdornment>
            ),
          }}
        />
      </Box>
    </Paper>
  );
}
