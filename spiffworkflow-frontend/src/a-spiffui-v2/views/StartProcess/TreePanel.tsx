import { Box, Paper, Stack, useTheme } from '@mui/material';
import { SimpleTreeView } from '@mui/x-tree-view/SimpleTreeView';
import { TreeItem } from '@mui/x-tree-view/TreeItem';

export default function TreePanel({
  processGroups,
}: {
  processGroups: Record<string, any>;
}) {
  const isDark = useTheme().palette.mode === 'dark';
  const treeItemStyle = {
    borderRadius: 1,
    minWidth: 20,
    maxHeight: 18,
    textAlign: 'center',
    fontWeight: 600,
    backgroundColor: isDark ? `background.paper` : `background.bluegreymedium`,
  };

  const buildTree = (groups: Record<string, any>[]) => {
    return groups.map((group: Record<string, any>) => (
      <TreeItem
        key={group.id}
        itemId={group.id}
        label={
          <Stack direction="row">
            <Box sx={{ width: '100%' }}>{group.display_name}</Box>
            <Box sx={treeItemStyle}>
              {(group?.process_models?.length || 0) +
                (group?.process_groups?.length || 0)}
            </Box>
          </Stack>
        }
      >
        {group?.process_models?.map((pm: Record<string, any>) => (
          <TreeItem key={pm.id} itemId={pm.id} label={pm.display_name} />
        ))}
        {group?.process_groups?.length > 0 && buildTree(group.process_groups)}
      </TreeItem>
    ));
  };
  return (
    <Paper
      elevation={0}
      sx={{
        width: '100%',
        height: 'calc(100vh - 75px)',
        borderRadius: 0,
        borderRight: 1,
        borderRightColor: 'divider',
        borderRightStyle: 'solid',
        padding: 2,
        overflowY: 'auto',
        overflowX: 'hidden',
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
  );
}
