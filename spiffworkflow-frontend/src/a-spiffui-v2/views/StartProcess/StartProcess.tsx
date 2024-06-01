import { useEffect } from 'react';

import useProcessGroups from '../../hooks/useProcessGroups';
import { Grid, Paper, Stack } from '@mui/material';
import { SimpleTreeView } from '@mui/x-tree-view/SimpleTreeView';
import { TreeItem } from '@mui/x-tree-view/TreeItem';

export default function StartProcess() {
  const { processGroups } = useProcessGroups({ processInfo: {} });

  useEffect(() => {
    if (processGroups?.results?.length) {
      console.log(processGroups);
    }
  }, [processGroups]);

  return (
    <Grid container sx={{ width: '100%', height: '100%' }}>
      <Grid item sx={{ width: '20%', height: '100%', paddingTop: 0.25 }}>
        <Paper
          elevation={0}
          sx={{
            width: '100%',
            height: '100%',
            borderRadius: 0,
            borderRight: 1,
            borderRightColor: 'divider',
            borderRightStyle: 'solid',
          }}
        >
          <SimpleTreeView
            sx={{
              '& .MuiTreeItem-label': {
                fontSize: '12px !important',
                color: 'text.secondary',
              },
            }}
          >
            <TreeItem itemId="grid" label="Data Grid">
              <TreeItem itemId="grid-community" label="@mui/x-data-grid" />
              <TreeItem itemId="grid-pro" label="@mui/x-data-grid-pro" />
              <TreeItem
                itemId="grid-premium"
                label="@mui/x-data-grid-premium"
              />
            </TreeItem>
            <TreeItem itemId="pickers" label="Date and Time Pickers">
              <TreeItem
                itemId="pickers-community"
                label="@mui/x-date-pickers"
              />
              <TreeItem itemId="pickers-pro" label="@mui/x-date-pickers-pro" />
            </TreeItem>
            <TreeItem itemId="charts" label="Charts">
              <TreeItem itemId="charts-community" label="@mui/x-charts" />
            </TreeItem>
            <TreeItem itemId="tree-view" label="Tree View">
              <TreeItem itemId="tree-view-community" label="@mui/x-tree-view" />
            </TreeItem>
          </SimpleTreeView>
        </Paper>
      </Grid>
      <Grid item>
        <Stack>
          <h1>Start Process</h1>
        </Stack>
      </Grid>
    </Grid>
  );
}
