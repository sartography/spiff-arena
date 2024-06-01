import { useEffect } from 'react';

import useProcessGroups from '../../hooks/useProcessGroups';
import { Grid, Paper, Stack } from '@mui/material';
import { SimpleTreeView } from '@mui/x-tree-view/SimpleTreeView';
import { TreeItem } from '@mui/x-tree-view/TreeItem';

export default function StartProcess() {
  const { processGroups } = useProcessGroups({ processInfo: {} });

  const buildTree = (groups: Record<string, any>[]) => {
    console.log(groups);
    return groups.map((group: Record<string, any>) => (
      <TreeItem key={group.id} itemId={group.id} label={group.display_name}>
        {group?.process_models?.map((pm: Record<string, any>) => (
          <TreeItem key={pm.id} itemId={pm.id} label={pm.display_name} />
        ))}
        {group?.process_groups?.length > 0 && buildTree(group.process_groups)}
      </TreeItem>
    ));
  };

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
            {processGroups?.results?.length && buildTree(processGroups.results)}
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
