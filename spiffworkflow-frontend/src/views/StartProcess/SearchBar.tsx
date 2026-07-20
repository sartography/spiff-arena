import {
  Box,
  FormControlLabel,
  InputAdornment,
  MenuItem,
  Paper,
  Switch,
  TextField,
} from '@mui/material';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import SearchOutlinedIcon from '@mui/icons-material/SearchOutlined';
import { Subject, Subscription } from 'rxjs';
import { ProcessModelSortOption } from '../../interfaces';

/**
 * Basic container for the search features in this view.
 */
export default function SearchBar({
  callback,
  stream,
  sortBy,
  onSortChange,
  showOnlyRun,
  onShowOnlyRunChange,
}: {
  callback: (search: string) => void;
  stream?: Subject<Record<string, any>>;
  sortBy: ProcessModelSortOption;
  onSortChange: (sort: ProcessModelSortOption) => void;
  showOnlyRun: boolean;
  onShowOnlyRunChange: (checked: boolean) => void;
}) {
  const { t } = useTranslation();
  const [searchText, setSearchText] = useState('');
  const bgPaper = 'background.paper';

  const handleSearchChange = (search: string) => {
    setSearchText(search);
    callback(search);
  };

  const handleClickStream = () => {
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
        boxSizing: 'border-box',
        display: 'flex',
        gap: 2,
        flexWrap: 'wrap',
        padding: 2,
        borderColor: `borders.primary`,
        borderWidth: 1,
        borderStyle: 'solid',
        alignItems: 'center',
      }}
    >
      <Box sx={{ flexGrow: 1, minWidth: { xs: '100%', sm: 240 } }}>
        <TextField
          size="small"
          sx={{
            width: '100%',
            backgroundColor: bgPaper,
          }}
          variant="outlined"
          placeholder={t('search_placeholder')}
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
      <TextField
        select
        size="small"
        label={t('sort_by')}
        value={sortBy}
        onChange={(e) => onSortChange(e.target.value as ProcessModelSortOption)}
        sx={{
          minWidth: { xs: '100%', sm: 160 },
          backgroundColor: bgPaper,
        }}
      >
        <MenuItem value="alphabetical">{t('alphabetical')}</MenuItem>
        <MenuItem value="recently_ran">{t('recently_ran')}</MenuItem>
        <MenuItem value="most_used">{t('most_used')}</MenuItem>
      </TextField>
      <FormControlLabel
        control={
          <Switch
            checked={showOnlyRun}
            onChange={(e) => onShowOnlyRunChange(e.target.checked)}
            size="small"
          />
        }
        label={t('has_been_run')}
        sx={{ whiteSpace: 'nowrap' }}
      />
    </Paper>
  );
}
