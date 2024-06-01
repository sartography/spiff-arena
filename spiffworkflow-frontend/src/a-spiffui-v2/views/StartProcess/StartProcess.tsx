import { Grid, Stack } from '@mui/material';
import useProcessGroups from '../../hooks/useProcessGroups';
import TreePanel from './TreePanel';

export default function StartProcess() {
  const { processGroups } = useProcessGroups({ processInfo: {} });
  return (
    <Grid container sx={{ width: '100%', height: '100%' }}>
      <Grid
        item
        sx={{
          width: '20%',
          minWidth: 250,
          maxWidth: 450,
          height: '100%',
          paddingTop: 0.25,
        }}
      >
        <TreePanel processGroups={processGroups} />
      </Grid>
      <Grid item>
        <Stack>
          <h1>Start Process</h1>
        </Stack>
      </Grid>
    </Grid>
  );
}
