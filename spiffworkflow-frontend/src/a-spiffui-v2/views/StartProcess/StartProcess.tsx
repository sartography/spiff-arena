import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Container,
  Stack,
} from '@mui/material';
import { useEffect, useRef, useState } from 'react';
import { Subject, Subscription } from 'rxjs';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import useProcessGroups from '../../hooks/useProcessGroups';
import TreePanel, { TreeRef, SHOW_FAVORITES } from './TreePanel';
import SearchBar from './SearchBar';
import ProcessGroupCard from './ProcessGroupCard';
import ProcessModelCard from './ProcessModelCard';
import { getStorageValue } from '../../services/LocalStorageService';
import { set } from 'date-fns';

export default function StartProcess() {
  const { processGroups } = useProcessGroups({ processInfo: {} });
  const [groups, setGroups] = useState<Record<string, any>[]>([]);
  const [models, setModels] = useState<Record<string, any>[]>([]);
  const [flatItems, setFlatItems] = useState<Record<string, any>[]>([]);
  // On load, there are always groups and never models, expand accordingly.
  const [groupsExpanded, setGroupsExpanded] = useState(true);
  const [modelsExpanded, setModelsExpanded] = useState(false);
  const [lastSelected, setLastSelected] = useState<Record<string, any>>({});
  const [crumbs, setCrumbs] = useState('');
  const treeRef = useRef<TreeRef>(null);
  const clickStream = new Subject<Record<string, any>>();
  const gridProps = {
    width: '100%',
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, 400px)',
    justifyContent: 'center',
    gridGap: 20,
  };

  const handleClickStream = (item: Record<string, any>) => {
    setCrumbs(item.id);
    setLastSelected(item);
    let itemToUse: any = { ...item };
    // Duck type to find out if this is a model ore a group.
    // If  model, we want its parent group, which can be found in the id.
    if (!('process_groups' in item)) {
      // recursively find the parent group.
      const findParent = (
        searchGroups: Record<string, any>[],
        id: string
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
      findParent(processGroups.results, parentId);
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
  };

  /** Tree calls back here so we can imperatively rework groups etc. */
  const handleFavorites = ({ text }: { text: string }) => {
    if (text === SHOW_FAVORITES) {
      const storage = JSON.parse(getStorageValue('spifffavorites'));
      const favs = flatItems.filter((item) => storage.includes(item.id));
      // If there's no favorites, the user is just left looking at nothing.
      // Load the top level groups instead.
      // Expand accordions accordingly (haha).
      setGroups(favs.length ? [] : processGroups.results);
      setModels(favs);
      setModelsExpanded(!!favs.length);
      setGroupsExpanded(!favs.length);
      setCrumbs('favorites');
    }

    return false;
  };

  /**
   * For now, we're just pasting together some info fields that make sense.
   * This is simple and works and is easily expanded,
   * but eventually might need to be more robust.
   */
  const handleSearch = (search: string) => {
    // Indicate to user this is a search result.
    setCrumbs(`Searching for: ${search || '(all)'}`);
    // Search the flattened items for the search term.
    const foundGroups = flatItems.filter((item) => {
      return (
        item.id.toLowerCase().includes(search.toLowerCase()) &&
        item?.process_groups
      );
    });
    const foundModels = flatItems.filter((item) => {
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
  };

  useEffect(() => {
    // If no favorites, proceed with the normal process groups.
    if (processGroups?.results) {
      // Recursively flatten the entire hierarchy of process groups and models
      // TODO: It would be VERY WISE to do this on init.
      const flattenAllItems = (
        items: Record<string, any>[],
        flat: Record<string, any>[]
      ) => {
        items.forEach((item) => {
          flat.push(item);
          // Duck type to see if it's a group, and if so, recurse.
          if (item.process_groups) {
            flattenAllItems(
              [...item.process_groups, ...item.process_models],
              flat
            );
          }
        });

        return flat;
      };

      /**
       * Do this now and put it in state.
       * You do not want to do this on every change to the search filter.
       * The flattened map makes searching globally simple.
       */
      const flattened = flattenAllItems(processGroups?.results || [], []);
      setFlatItems(flattened);

      // If there are favorites, that's all we want to display, return.
      const favorites = JSON.parse(getStorageValue('spifffavorites'));
      if (favorites.length) {
        setModels(flattened.filter((item) => favorites.includes(item.id)));
        setGroups([]);
        setModelsExpanded(true);
        setGroupsExpanded(false);
        setCrumbs('favorites');
        return;
      }
      setGroups(processGroups.results);
      setGroupsExpanded(!!processGroups.results.length);
    }
  }, [processGroups]);

  let cardStreamSub: Subscription;
  useEffect(() => {
    if (!cardStreamSub && clickStream) {
      clickStream.subscribe(handleClickStream);
    }
  }, [clickStream]);

  return (
    <Container
      maxWidth={false}
      sx={{
        padding: '0px !important',
        overflow: 'hidden',
      }}
    >
      <Stack direction="row">
        <Box
          sx={{
            minWidth: 250,
            maxWidth: 450,
            width: '20%',
            paddingTop: 0.25,
          }}
        >
          <TreePanel
            ref={treeRef}
            processGroups={processGroups}
            stream={clickStream}
            callback={() => handleFavorites({ text: SHOW_FAVORITES })}
          />
        </Box>
        <Stack
          sx={{
            width: '100%',
          }}
        >
          <Stack
            gap={2}
            sx={{
              width: '100%',
              height: '100%',
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
                height: 'calc(100vh - 180px)',
                overflowY: 'auto',
                overflowX: 'hidden',
                padding: 0,
              }}
            >
              <Stack
                gap={4}
                sx={{
                  padding: 2,
                }}
              >
                <Box>
                  {crumbs && <Box>{crumbs}</Box>}
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
                            model={model}
                            stream={clickStream}
                            lastSelected={lastSelected}
                          />
                        ))}
                      </Box>
                    </AccordionDetails>
                  </Accordion>
                </Box>
                <Accordion
                  expanded={groupsExpanded}
                  onChange={() => setGroupsExpanded((prev) => !prev)}
                >
                  <AccordionSummary
                    expandIcon={<ExpandMoreIcon />}
                    aria-controls="Process Groups Accordion"
                  >
                    ({groups.length}) Process Groups
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box sx={gridProps}>
                      {groups.map((group: Record<string, any>) => (
                        <ProcessGroupCard group={group} stream={clickStream} />
                      ))}
                    </Box>
                  </AccordionDetails>
                </Accordion>
              </Stack>
            </Stack>
          </Stack>
        </Stack>
      </Stack>
    </Container>
  );
}
