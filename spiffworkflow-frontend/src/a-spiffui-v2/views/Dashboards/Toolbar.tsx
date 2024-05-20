import { Typography, Button, Grid, Box } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';

/** Appears at the top of the Dashboards view. */
export default function Toolbar() {
  const showTime = () => {
    return new Date().toDateString();
  };

  return (
    <Grid container>
      <Grid item xs={2}>
        <Typography variant="h4" color="text.primary">
          Dashboards
        </Typography>
        <Typography variant="caption" color="text.secondary" noWrap>
          Last Updated: {showTime()}
        </Typography>
      </Grid>
      <Grid item xs={12} sm={10}>
        <Box
          sx={{
            display: { xs: 'none', md: 'flex' },
            justifyContent: { xs: '', sm: 'flex-end' },
            alignItems: 'center',
            height: '100%',
          }}
          gap={2}
        >
          <Button
            title="Start New Process"
            variant="contained"
            startIcon={<AddIcon />}
            sx={{ width: 200, height: 40 }}
          >
            Start New Process
          </Button>
        </Box>
      </Grid>
    </Grid>
  );
}
