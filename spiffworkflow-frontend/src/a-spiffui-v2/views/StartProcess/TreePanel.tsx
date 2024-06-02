import { Box, Divider, Paper, Stack, useTheme } from '@mui/material';
import { SimpleTreeView } from '@mui/x-tree-view/SimpleTreeView';
import { TreeItem } from '@mui/x-tree-view/TreeItem';
import StarRateIcon from '@mui/icons-material/StarRate';
import HistoryIcon from '@mui/icons-material/History';
import MenuItem from '../app/topmenu/MenuItem';

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
      <Stack gap={2} sx={{ justifyContent: 'left' }}>
        <Box>
          <MenuItem
            data={{
              text: 'Favorites',
              icon: (
                <StarRateIcon
                  sx={{ transform: 'scale(.8)', color: 'spotColors.goldStar' }}
                />
              ),
              path: '',
              align: 'flex-start',
            }}
            callback={() => {}}
          />
          <MenuItem
            data={{
              text: 'Recently Used',
              icon: <HistoryIcon sx={{ transform: 'scale(.8)' }} />,
              path: '',
              align: 'flex-start',
            }}
            callback={() => {}}
          />
        </Box>
        <Divider
          sx={{
            backgroundColor: isDark ? 'primary.main' : 'background.dark',
          }}
        />
        {/** Have to force this for design requirement */}
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
      </Stack>
    </Paper>
  );
}
