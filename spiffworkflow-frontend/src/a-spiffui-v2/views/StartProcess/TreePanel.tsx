import { Box, Divider, Paper, Stack, useTheme } from '@mui/material';
import { SimpleTreeView } from '@mui/x-tree-view/SimpleTreeView';
import { TreeItem } from '@mui/x-tree-view/TreeItem';
import StarRateIcon from '@mui/icons-material/StarRate';
import HistoryIcon from '@mui/icons-material/History';
import { Subject, Subscription } from 'rxjs';
import { forwardRef, useEffect, useImperativeHandle, useState } from 'react';
import MenuItem from '../app/topmenu/MenuItem';
import { SPIFF_FAVORITES } from '../../services/LocalStorageService';

export const SHOW_FAVORITES = 'SHOW_FAVORITES';

export type TreeRef = {
  clearExpanded: () => void;
};

/**
 * Display and control a MUI tree in the UI.
 * This is a bit of a beast, as it has to manage its own state,
 * and all of the expand/collapse is explict because it has to track
 * with the card navigation in the parent view (via streams etc.).
 */
export default forwardRef(function TreePanel(
  {
    processGroups,
    callback,
    stream,
  }: {
    processGroups: Record<string, any>;
    callback?: (data: Record<string, any>) => void;
    stream?: Subject<Record<string, any>>;
  },
  ref: any, // can literally be anything that wants to clear the tree
) {
  const [expanded, setExpanded] = useState<string[]>([]);
  const [lastSelected, setLastSelected] = useState<Record<string, any>>({});
  const [favoriteCount, setFavoriteCount] = useState(0);
  const isDark = useTheme().palette.mode === 'dark';

  const treeItemStyle = {
    borderRadius: 1,
    width: 50,
    maxHeight: 18,
    textAlign: 'center',
    fontWeight: 600,
    backgroundColor: isDark ? `background.paper` : `background.bluegreymedium`,
  };

  /** We allow imperatively clearing the expanded items of the tree via a forwardRef */
  useImperativeHandle(ref, () => ({
    clearExpanded: () => {
      setExpanded([]);
      setLastSelected({});
    },
  }));

  /**
   * There is a lot of style wrangling on the tree items.
   * We've taken control of the expand/collapse of the tree,
   * becase we want to expand/collapse and highlight nodes that correspond to an external clickStream.
   * (For now, that comes from the parent, StartProcess.tsx, that owns the stream).
   * The downside is, once you take control of anything having to do with how the tree works,
   * You have to manage it all yourself.
   */
  const buildTree = (groups: Record<string, any>[]) => {
    return groups.map((group: Record<string, any>) => (
      <TreeItem
        key={group.id}
        itemId={group.id}
        onClick={() => stream && stream.next(group)}
        label={
          <Stack
            direction="row"
            sx={{
              backgroundColor:
                lastSelected.id === group.id
                  ? 'spotColors.selectedBackground'
                  : '',
              padding: 0.5,
              borderRadius: 1,
            }}
          >
            <Box sx={{ width: '100%' }}>{group.display_name}</Box>
            <Box sx={treeItemStyle}>
              {`${group?.process_models?.length || 0} / 
                ${group?.process_groups?.length || 0}`}
            </Box>
          </Stack>
        }
      >
        {group?.process_models?.map((model: Record<string, any>) => (
          <TreeItem
            key={model.id}
            itemId={model.id}
            label={
              <Box
                sx={{
                  backgroundColor:
                    lastSelected.id === model.id
                      ? 'spotColors.selectedBackground'
                      : '',
                  padding: 0.5,
                  borderRadius: 1,
                }}
              >
                {model.display_name}
              </Box>
            }
            onClick={() => stream && stream.next(model)}
          />
        ))}
        {group?.process_groups?.length > 0 && buildTree(group.process_groups)}
      </TreeItem>
    ));
  };

  const expandToItem = (item: Record<string, any>) => {
    if (!item) {
      return;
    }
    /**
     * A given item will look like group/another_group/another_group/model
     * The parent path of each item is the path to the item, minus the last id.
     * So from a single id we can build the path hieararchy to this item.
     */
    const newExpanded: string[] = [];
    const split: string[] = item.id.split('/');
    split.forEach((id, i) => {
      newExpanded.push(i === 0 ? id : `${newExpanded[i - 1]}/${id}`);
    });
    /**
     * If this was a leaf node, we don't want to try to expand it.
     * TODO: Get types together for this one day.
     */
    if (!('process_models' in item)) {
      newExpanded.pop();
    }

    // Less buggy to remove all duplicates instead of trying to prevent them.
    const removeDupes = new Set([...expanded, ...newExpanded]);
    setExpanded(Array.from(removeDupes));
  };

  let streamSub: Subscription;
  useEffect(() => {
    if (!streamSub && stream) {
      // eslint-disable-next-line react-hooks/exhaustive-deps
      streamSub = stream.subscribe((item) => {
        setLastSelected({ ...item });
      });
    }

    /**
     * Any stream update could be adding a new favorite, so recalculate the count.
     * TODO: Some form of this is a candidate for a hook.
     */
    const favorites = JSON.parse(localStorage.getItem(SPIFF_FAVORITES) || '[]');
    setFavoriteCount(favorites.length);
  }, [stream]);

  /**
   * This needs to happen independently of the subscription callback,
   * which is async, setting it directly in that way will not propagate the state
   * (This is why we have a separate useEffect)
   */
  useEffect(() => {
    if (!lastSelected?.id) {
      return;
    }
    /**
     * First, let's see if the item is already expanded.
     * If it is, we want to collapse it and do nothing else.
     */
    if (expanded.find((n) => n === lastSelected.id)) {
      const removePath = expanded.filter((id) => id !== lastSelected.id);
      setExpanded(() => [...removePath]);
      return;
    }

    console.log(lastSelected);
    // Otherwise, go through the rigamarole of expanding it.
    expandToItem(lastSelected);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lastSelected]);

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
          <Stack direction="row" sx={{ alignItems: 'center', paddingRight: 2 }}>
            <MenuItem
              data={{
                text: `Favorites`,
                icon: (
                  <StarRateIcon
                    sx={{
                      transform: 'scale(.8)',
                      color: 'spotColors.goldStar',
                    }}
                  />
                ),
                path: '',
                align: 'flex-start',
              }}
              callback={() => callback && callback({ text: SHOW_FAVORITES })}
            />
            <Box sx={{ ...treeItemStyle, fontSize: 10, width: 30 }}>
              {favoriteCount}
            </Box>
          </Stack>
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
});
