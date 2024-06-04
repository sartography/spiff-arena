import { Box, Divider, Paper, Stack, useTheme } from '@mui/material';
import { SimpleTreeView } from '@mui/x-tree-view/SimpleTreeView';
import { TreeItem } from '@mui/x-tree-view/TreeItem';
import StarRateIcon from '@mui/icons-material/StarRate';
import HistoryIcon from '@mui/icons-material/History';
import { Subject, Subscription } from 'rxjs';
import MenuItem from '../app/topmenu/MenuItem';
import { useEffect, useState } from 'react';

export default function TreePanel({
  processGroups,
  stream,
}: {
  processGroups: Record<string, any>;
  stream?: Subject<Record<string, any>>;
}) {
  const [expanded, setExpanded] = useState<string[]>([]);
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
        onClick={() => stream && stream.next(group)}
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
        {group?.process_models?.map((model: Record<string, any>) => (
          <TreeItem
            key={model.id}
            itemId={model.id}
            label={model.display_name}
            onClick={() => stream && stream.next(model)}
          />
        ))}
        {group?.process_groups?.length > 0 && buildTree(group.process_groups)}
      </TreeItem>
    ));
  };

  const expandToItem = (item: Record<string, any>) => {
    if (item) {
      const newExpanded: string[] = [];
      const split: string[] = item.id.split('/');
      split.forEach((id, i) => {
        newExpanded.push(i === 0 ? id : `${newExpanded[i - 1]}/${id}`);
      });
      // Expand logic is working, need to work on the collapse side of this.
      setExpanded(newExpanded);
    }
  };

  let streamSub: Subscription;
  useEffect(() => {
    if (!streamSub && stream) {
      streamSub = stream.subscribe((item) => {
        expandToItem(item);
      });
    }
  }, [stream]);

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
          expandedItems={expanded}
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
