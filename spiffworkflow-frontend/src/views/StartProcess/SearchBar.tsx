import { Box, InputAdornment, Paper, TextField } from '@mui/material';
import { useEffect, useState } from 'react';
import SearchOutlinedIcon from '@mui/icons-material/SearchOutlined';
import { Subject, Subscription } from 'rxjs';

/**
 * Basic container for the search features in this view.
 */
export default function SearchBar({
  callback,
  stream,
}: {
  callback: (search: string) => void;
  stream?: Subject<Record<string, any>>;
}) {
  const [searchText, setSearchText] = useState('');
  const bgPaper = 'background.paper';

  const handleSearchChange = (search: string) => {
    setSearchText(search);
    callback(search);
  };

  const handleClickStream = () => {
    /**
     * Bespoke behavior:
     * If a card or tree node is clicked, that takes over the display.
     * Wipe the search value.
     */
    setSearchText('');
  };

  let streamSub: Subscription;
  useEffect(() => {
    if (!streamSub && stream) {
      // eslint-disable-next-line react-hooks/exhaustive-deps
      streamSub = stream.subscribe(handleClickStream);
    }

    return () => {
      streamSub.unsubscribe();
    };
  }, [stream]);

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
