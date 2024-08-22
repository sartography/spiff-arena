import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Container,
  Stack,
  Typography,
} from '@mui/material';
import { useEffect, useRef, useState } from 'react';
import { Subject, Subscription } from 'rxjs';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import StarRateIcon from '@mui/icons-material/StarRate';
import { useDebouncedCallback } from 'use-debounce';
import useProcessGroups from '../../hooks/useProcessGroups';
import TreePanel, { TreeRef, SHOW_FAVORITES } from './TreePanel';
import SearchBar from './SearchBar';
import ProcessGroupCard from './ProcessGroupCard';
import ProcessModelCard from './ProcessModelCard';
import {
  SPIFF_FAVORITES,
  getStorageValue,
} from '../../services/LocalStorageService';
import SpiffBreadCrumbs, { Crumb, SPIFF_ID } from './SpiffBreadCrumbs';
import { modifyProcessIdentifierForPathParam } from '../../../helpers';
import { ProcessGroup, ProcessGroupLite } from '../../../interfaces';

type OwnProps = {
  setNavElementCallback: Function;
};
/**
 * Top level layout and control container for this view,
 * feeds various streams, data and callbacks to children.
 */
export default function StartProcess({ setNavElementCallback }: OwnProps) {
  const { processGroups } = useProcessGroups({
    processInfo: {},
    getRunnableProcessModels: true,
  });
  const [groups, setGroups] = useState<
    ProcessGroup[] | ProcessGroupLite[] | null
  >(null);
  const [models, setModels] = useState<Record<string, any>[]>([]);
  const [flatItems, setFlatItems] = useState<Record<string, any>>([]);
  // On load, there are always groups and never models, expand accordingly.
  const [groupsExpanded, setGroupsExpanded] = useState(true);
  const [modelsExpanded, setModelsExpanded] = useState(false);
  const [lastSelected, setLastSelected] = useState<Record<string, any>>({});
  const [crumbs, setCrumbs] = useState<Crumb[]>([]);
  // const [treeCollapsed, setTreeCollapsed] = useState(false);
  const [treeCollapsed] = useState(false);
  const treeRef = useRef<TreeRef>(null);
  // Pass to anything that wants to broadcast to all subscribers
  const clickStream = new Subject<Record<string, any>>();
  const favoriteCrumb: Crumb = { id: 'favorites', displayName: 'Favorites' };
  const gridProps = {
    width: '100%',
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, 400px)',
    justifyContent: 'center',
    gridGap: 20,
  };

  const processCrumbs = (item: Record<string, any>): Crumb[] => {
    /**
     * Create the paths for the crumbs.
     * This logic is repeated from TreePanel.
     * TODO: Consider a service, or hook, or something.
     */
    const pathIds: string[] = [];
    const split: string[] = item.id.split('/');
    split.forEach((id, i) => {
      pathIds.push(i === 0 ? id : `${pathIds[i - 1]}/${id}`);
    });

    // Look up the display names in the flattened items and return.
    return pathIds.map((id) => {
      const found = flatItems.find((flatItem: any) => flatItem.id === id);
      return { id, displayName: found?.display_name || id };
    });
  };

  const handleClickStream = (item: Record<string, any>) => {
    setCrumbs(processCrumbs(item));
    setLastSelected(item);
    let itemToUse: any = { ...item };
    // Duck type to find out if this is a model ore a group.
    // If  model, we want its parent group, which can be found in the id.
    if (!('process_groups' in item)) {
      // recursively find the parent group.
      const findParent = (
        searchGroups: Record<string, any>[],
        id: string,
      ): Record<string, any> | undefined => {
        return searchGroups.find((group) => {
          if (group.id === id) {
            itemToUse = group;
            return group;
          }
          if (group.process_groups) {
            return findParent(group.process_groups, id);
          }

          return false;
        });
      };
      // Remove the last part of the id, which is not and expandable entity.
      const parentId = item.id.split('/').slice(0, -1).join('/');
      findParent(processGroups || [], parentId);
    }

    if (itemToUse?.process_models) {
      // If a user clicks a group, and it has models, expand them for the user.
      if (itemToUse.process_models.length) {
        setModelsExpanded(true);
      }
      setModels(itemToUse.process_models);
    }

    // If there are groups in this group, set them into state for display
    if (itemToUse?.process_groups) {
      setGroups(itemToUse.process_groups);
    }

    const container = document.getElementById('scrollable-process-card-area');
    const cardElement = document.getElementById(
      `card-${modifyProcessIdentifierForPathParam(item.id)}`,
    );
    if (container && cardElement) {
      setTimeout(() => {
        container.scrollTo({
          top: cardElement.offsetTop - container.offsetTop,
          behavior: 'smooth',
        });
      }, 100); // Slight delay before scrolling to ensure rendering
    }
  };

  /** Tree calls back here so we can imperatively rework groups etc. */
  const handleFavorites = ({ text }: { text: string }) => {
    if (text === SHOW_FAVORITES) {
      const storage = JSON.parse(getStorageValue('spifffavorites'));
      const favs = flatItems.filter((item: any) => storage.includes(item.id));
      // If there's no favorites, the user is just left looking at nothing.
      // Load the top level groups instead.
      // Expand accordions accordingly (haha).
      setGroups(favs.length ? [] : processGroups);
      setModels(favs);
      setModelsExpanded(!!favs.length);
      setGroupsExpanded(!favs.length);
      setCrumbs([favoriteCrumb]);
    }

    return false;
  };

  /**
   * For now, we're just pasting together some info fields that make sense.
   * This is simple and works and is easily expanded,
   * but eventually might need to be more robust.
   */
  const handleSearch = useDebouncedCallback((search: string) => {
    // Indicate to user this is a search result.
    setCrumbs([
      { id: search, displayName: `Searching for: ${search || '(all)'}` },
    ]);
    // Search the flattened items for the search term.
    const foundGroups = flatItems.filter((item: any) => {
      return (
        item.id.toLowerCase().includes(search.toLowerCase()) &&
        item?.process_groups
      );
    });
    const foundModels = flatItems.filter((item: any) => {
      return (
        (item.id + item.display_name + item.description)
          .toLowerCase()
          .includes(search.toLowerCase()) && !item?.process_groups
      );
    });

    setGroups(foundGroups);
    setGroupsExpanded(!!foundGroups.length);
    setModels(foundModels);
    setModelsExpanded(!!foundModels.length);
    // The tree isn't connected to these results, so imperatively wipe the expanded nodes.
    treeRef.current?.clearExpanded();
  }, 250);

  /**
   * When a crumb is clicked, we need to find the item in the flatItems list
   * and feed it to the clickstream.
   */
  const handleCrumbClick = (crumb: Crumb) => {
    // If this is s top-level crumb, just reset the view.
    if (crumb.id === SPIFF_ID) {
      setGroups(processGroups);
      setModels([]);
      setModelsExpanded(false);
      setGroupsExpanded(true);
      setCrumbs([]);
      treeRef.current?.clearExpanded();
      return;
    }
    // Otherwise, find the item in the flatItems list and feed it to the clickstream.
    const found = flatItems.find((item: any) => item.id === crumb.id);
    if (found) {
      clickStream.next(found);
    }
  };

  /** Recursively flatten the entire hierarchy of process groups and models */
  const flattenAllItems = (items: ProcessGroup[], flat: ProcessGroup[]) => {
    items.forEach((item) => {
      flat.push(item);
      // Duck type to see if it's a group, and if so, recurse.
      if (item.process_groups) {
        flattenAllItems(
          [...item.process_groups, ...(item.process_models || [])],
          flat,
        );
      }
    });

    return flat;
  };

  useEffect(() => {
    // If no favorites, proceed with the normal process groups.
    if (processGroups) {
      /**
       * Do this now and put it in state.
       * You do not want to do this on every change to the search filter.
       * The flattened map makes searching globally simple.
       */
      const flattened = flattenAllItems(processGroups || [], []);
      setFlatItems(flattened);

      // If there are favorites, that's all we want to display, return.
      const favorites = JSON.parse(getStorageValue(SPIFF_FAVORITES));
      if (favorites.length) {
        setModels(flattened.filter((item) => favorites.includes(item.id)));
        setGroups([]);
        setModelsExpanded(true);
        setGroupsExpanded(false);
        setCrumbs([favoriteCrumb]);
        return;
      }
      setGroups(processGroups);
      setGroupsExpanded(!!processGroups.length);
      setCrumbs([]);
      if (setNavElementCallback) {
        setNavElementCallback(
          <TreePanel
            ref={treeRef}
            processGroups={processGroups}
            stream={clickStream}
            // callback={() => handleFavorites({ text: SHOW_FAVORITES })}
          />,
        );
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [processGroups]);

  let cardStreamSub: Subscription;
  useEffect(() => {
    if (!cardStreamSub && clickStream) {
      clickStream.subscribe(handleClickStream);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clickStream]);

  return (
    <Box
      component="main"
      sx={{
        flexGrow: 1,
        p: 3,
        overflow: 'hidden',
        height: '100vh',
      }}
    >
      <Typography variant="h1" sx={{ mb: 2 }}>
        Start new process
      </Typography>
      <Container
        maxWidth={false}
        sx={{
          padding: '0px !important',
          overflow: 'hidden',
          height: '100vh',
        }}
        id="list-container"
      >
        <Stack
          gap={2}
          sx={{
            width: '100%',
            height: '100vh',
            display: 'flex',
            alignItems: 'center',
          }}
        >
          <Stack
            direction="row"
            sx={{
              width: '100%',
              paddingTop: 2,
              paddingLeft: 2,
              paddingRight: 2,
              justifyContent: 'center',
            }}
          >
            <SearchBar callback={handleSearch} stream={clickStream} />
          </Stack>

          <Stack
            sx={{
              width: '100%',
              overflowY: 'auto',
              overflowX: 'hidden',
              paddingLeft: 2,
              paddingRight: 2,
            }}
            id="scrollable-process-card-area"
          >
            <Stack direction="row" gap={1} sx={{ paddingBottom: 0.5 }}>
              {treeCollapsed && (
                <Stack
                  direction="row"
                  gap={1}
                  sx={{
                    backgroundColor: 'background.paper',
                    border: '1px solid',
                    borderColor: 'borders.primary',
                    borderRadius: 1,
                    alignItems: 'center',
                    paddingRight: 2,
                    position: 'relative',
                    cursor: 'pointer',
                  }}
                  onClick={() => handleFavorites({ text: SHOW_FAVORITES })}
                >
                  <StarRateIcon
                    sx={{
                      transform: 'scale(.8)',
                      color: 'spotColors.goldStar',
                      position: 'relative',
                      top: -1,
                    }}
                  />
                  <Typography variant="caption">Favorites</Typography>
                </Stack>
              )}
              <SpiffBreadCrumbs crumbs={crumbs} callback={handleCrumbClick} />
            </Stack>
            <Accordion
              expanded={modelsExpanded}
              onChange={() => setModelsExpanded((prev) => !prev)}
            >
              <AccordionSummary
                expandIcon={<ExpandMoreIcon />}
                aria-controls="Process Models Accordion"
              >
                ({models.length}) Process Models
              </AccordionSummary>
              <AccordionDetails>
                <Box sx={gridProps}>
                  {models.map((model: Record<string, any>) => (
                    <ProcessModelCard
                      key={model.id}
                      model={model}
                      stream={clickStream}
                      lastSelected={lastSelected}
                      onStartProcess={() => {
                        // remove the TreePanel from the SideNav when starting a process
                        setNavElementCallback(null);
                      }}
                    />
                  ))}
                </Box>
              </AccordionDetails>
            </Accordion>
            <Accordion
              expanded={groupsExpanded}
              onChange={() => setGroupsExpanded((prev) => !prev)}
            >
              <AccordionSummary
                expandIcon={<ExpandMoreIcon />}
                aria-controls="Process Groups Accordion"
              >
                ({groups?.length}) Process Groups
              </AccordionSummary>
              <AccordionDetails>
                <Box sx={gridProps}>
                  {groups?.map((group: Record<string, any>) => (
                    <ProcessGroupCard
                      key={group.id}
                      group={group}
                      stream={clickStream}
                    />
                  ))}
                </Box>
              </AccordionDetails>
            </Accordion>
          </Stack>
        </Stack>
      </Container>
    </Box>
  );
}
