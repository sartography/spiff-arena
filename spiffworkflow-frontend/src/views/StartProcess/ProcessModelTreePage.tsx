import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Container,
  IconButton,
  Stack,
  Typography,
  Breadcrumbs,
  Link,
  Card,
  CardContent,
  Button,
} from '@mui/material';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Can } from '@casl/react';
import { Subject } from 'rxjs';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import StarRateIcon from '@mui/icons-material/StarRate';
import { Delete, Edit, Add, Home } from '@mui/icons-material';
import { useDebouncedCallback } from 'use-debounce';
import { useParams, useNavigate } from 'react-router';
import useProcessGroups from '../../hooks/useProcessGroups';
import TreePanel, { TreeRef, SHOW_FAVORITES } from './TreePanel';
import SearchBar from './SearchBar';
import ProcessGroupCard from './ProcessGroupCard';
import ProcessModelCard from './ProcessModelCard';
import {
  SPIFF_FAVORITES,
  getStorageValue,
} from '../../services/LocalStorageService';
import {
  PermissionsToCheck,
  ProcessGroup,
  ProcessGroupLite,
  DataStore,
  ProcessModel,
} from '../../interfaces';
import {
  modifyProcessIdentifierForPathParam,
  unModifyProcessIdentifierForPathParam,
} from '../../helpers';
import { useUriListForPermissions } from '../../hooks/UriListForPermissions';
import { usePermissionFetcher } from '../../hooks/PermissionService';
import ButtonWithConfirmation from '../../components/ButtonWithConfirmation';
import HttpService from '../../services/HttpService';
import DataStoreCard from '../../components/DataStoreCard';

const SPIFF_ID = 'spifftop';
type Crumb = { id: string; displayName: string };

type OwnProps = {
  setNavElementCallback?: Function;
  navigateToPage?: boolean;
};

/**
 * Converts a ProcessGroup to a ProcessGroupLite.
 */
const processGroupToLite = (group: ProcessGroup): ProcessGroupLite => {
  return {
    id: group.id,
    display_name: group.display_name,
    description: group.description || '', // Ensure description is not undefined
    process_models: group.process_models,
    process_groups: group.process_groups
      ? group.process_groups.map(processGroupToLite)
      : undefined,
  };
};

/**
 * Top level layout and control container for this view,
 * feeds various streams, data and callbacks to children.
 */
export default function ProcessModelTreePage({
  setNavElementCallback,
  navigateToPage = false,
}: OwnProps) {
  const params = useParams();
  const navigate = useNavigate();
  const { processGroups } = useProcessGroups({ processInfo: {} });
  const [groups, setGroups] = useState<
    ProcessGroup[] | ProcessGroupLite[] | null
  >(null);
  const [models, setModels] = useState<ProcessModel[]>([]);
  const [dataStores, setDataStores] = useState<DataStore[]>([]);
  const [flatItems, setFlatItems] = useState<Record<string, any>>([]);
  // On load, there are always groups and never models, expand accordingly.
  const [groupsExpanded, setGroupsExpanded] = useState(true);
  const [dataStoreExpanded, setDataStoreExpanded] = useState(true);
  const [modelsExpanded, setModelsExpanded] = useState(false);
  const [currentProcessGroup, setCurrentProcessGroup] = useState<Record<
    string,
    any
  > | null>(null);
  const [crumbs, setCrumbs] = useState<Crumb[]>([]);
  // const [treeCollapsed, setTreeCollapsed] = useState(false);
  const [treeCollapsed] = useState(false);
  const treeRef = useRef<TreeRef>(null);
  // Use useRef to maintain a stable stream instance across re-renders
  const clickStream = useRef(new Subject<Record<string, any>>()).current;
  const favoriteCrumb: Crumb = { id: 'favorites', displayName: 'Favorites' };
  const gridProps = {
    display: 'grid',
    gridGap: 20, // Spacing between cards
    gridTemplateColumns: {
      xs: '1fr', // Full width cards on extra-small screens
      sm: 'repeat(auto-fill, minmax(300px, 1fr))', // Smaller cards, responsive from 300px
      md: 'repeat(auto-fill, 400px)', // 400px wide cards on medium+ screens
    },
    justifyContent: 'center', // Center when there’s extra space
  };

  const { targetUris } = useUriListForPermissions();
  const permissionRequestData: PermissionsToCheck = {
    [targetUris.dataStoreListPath]: ['GET'],
    [targetUris.processGroupListPath]: ['POST'],
    [targetUris.processGroupShowPath]: ['PUT', 'DELETE'],
    [targetUris.processModelCreatePath]: ['POST'],
  };
  const { ability, permissionsLoaded } = usePermissionFetcher(
    permissionRequestData,
  );

  /** Recursively flatten the entire hierarchy of process groups and models */
  const flattenAllItems = useCallback(
    (items: ProcessGroup[], flat: ProcessGroup[]) => {
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
    },
    [],
  );

  const processCrumbs = (
    item: Record<string, any>,
    flattened: Record<string, any>,
  ): Crumb[] => {
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
      const found = flattened.find((flatItem: any) => flatItem.id === id);
      return { id, displayName: found?.display_name || id };
    });
  };

  const [clickedItem, setClickedItem] = useState<Record<string, any> | null>(
    null,
  );

  const handleClickStream = (item: Record<string, any>) => {
    setClickedItem(item);
  };

  function findProcessGroupByPath(
    groupsToProcess: ProcessGroupLite[] | null,
    path: string,
  ): ProcessGroupLite | undefined {
    const levels = path.split('/');
    let currentGroup: ProcessGroupLite | undefined;

    let newGroups: ProcessGroupLite[] = [];
    if (groupsToProcess) {
      newGroups = groupsToProcess;
    }

    levels.forEach((level: string) => {
      const assembledPath = levels
        .slice(0, levels.indexOf(level) + 1)
        .join('/');
      currentGroup = newGroups.find(
        (processGroup: any) => processGroup.id === assembledPath,
      );
      if (!currentGroup) {
        return undefined;
      }
      newGroups = currentGroup.process_groups || [];
      return currentGroup;
    });
    return currentGroup;
  }

  useEffect(() => {
    if (!clickedItem || !processGroups) {
      return;
    }

    const handleScrollTo = () => {
      const container = document.getElementById('scrollable-process-card-area');
      const cardElement = document.getElementById(
        `card-${modifyProcessIdentifierForPathParam(clickedItem.id)}`,
      );
      if (container && cardElement) {
        setTimeout(() => {
          container.scrollTo({
            top: cardElement.offsetTop - container.offsetTop,
            behavior: 'smooth',
          });
        }, 100);
      }
    };

    const setProcessGroupItems = (itemToUse: ProcessGroupLite) => {
      if (itemToUse?.process_models) {
        setModelsExpanded(!!itemToUse.process_models.length);
        setModels(itemToUse.process_models);
      }
      if (itemToUse?.process_groups) {
        setGroups(itemToUse.process_groups);
      }
      setCurrentProcessGroup(itemToUse);
    };

    const isProcessGroup = 'process_groups' in clickedItem;
    let itemToUse: any = { ...clickedItem };

    // Handle process model parent group lookup
    if (!isProcessGroup) {
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

      const parentId = clickedItem.id.split('/').slice(0, -1).join('/');
      findParent(processGroups || [], parentId);
    }

    setProcessGroupItems(itemToUse);
    handleScrollTo();

    if (isProcessGroup) {
      const flattened = flattenAllItems(processGroups, []);
      setCrumbs(processCrumbs(itemToUse, flattened));
      navigate(
        `/process-groups/${modifyProcessIdentifierForPathParam(itemToUse.id)}`,
      );
    }

    setClickedItem(null);
  }, [clickedItem, processGroups, navigate, flattenAllItems]);

  useEffect(() => {
    // If no favorites, proceed with the normal process groups.
    if (processGroups && permissionsLoaded) {
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
        // favorites currently do not work and flattened seems to be ProcessGroup[] and not models
        // setModels(flattened.filter((item) => favorites.includes(item.id)));
        setGroups([]);
        setModelsExpanded(true);
        setGroupsExpanded(false);
        setCrumbs([favoriteCrumb]);
        return;
      }
      const unModifiedProcessGroupId = unModifyProcessIdentifierForPathParam(
        `${params.process_group_id}`,
      );
      const processGroupsLite: ProcessGroupLite[] =
        processGroups.map(processGroupToLite);
      const foundProcessGroup = findProcessGroupByPath(
        processGroupsLite,
        unModifiedProcessGroupId,
      );
      if (foundProcessGroup) {
        setGroups(foundProcessGroup.process_groups || null);
        setModels(foundProcessGroup.process_models || []);
        setCrumbs(processCrumbs(foundProcessGroup, flattened));
        setCurrentProcessGroup(foundProcessGroup);
      } else {
        setGroups(processGroupsLite);
        setCrumbs([]);
      }
      setGroupsExpanded(!!processGroupsLite.length);
      if (ability.can('GET', targetUris.dataStoreListPath)) {
        HttpService.makeCallToBackend({
          path: '/data-stores',
          successCallback: (results: DataStore[]) => {
            setDataStores(results);
          },
        });
      }
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
  }, [processGroups, permissionsLoaded, ability]);

  useEffect(() => {
    if (clickStream) {
      clickStream.subscribe(handleClickStream);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clickStream]);

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

  // taken from ProcessModelSearch
  const getParentGroupsDisplayName = (
    processItem: ProcessModel | ProcessGroup,
  ) => {
    if (processItem.parent_groups) {
      return processItem.parent_groups
        .map((parentGroup: ProcessGroupLite) => {
          return parentGroup.display_name;
        })
        .join(' / ');
    }
    return '';
  };
  const getProcessModelLabelForSearch = (
    processItem: ProcessModel | ProcessGroup,
  ) => {
    return `${processItem.display_name} ${
      processItem.id
    } ${getParentGroupsDisplayName(processItem)}`;
  };
  const shouldFilterProcessModel = (
    processItem: ProcessModel,
    inputValue: string,
  ) => {
    const inputValueArray = inputValue.split(' ');
    const processModelLowerCase =
      getProcessModelLabelForSearch(processItem).toLowerCase();

    return inputValueArray.every((i: any) => {
      return processModelLowerCase.includes((i || '').toLowerCase());
    });
  };
  /// ////

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
      return shouldFilterProcessModel(item, search) && 'process_groups' in item;
    });
    const foundModels = flatItems.filter((item: any) => {
      return (
        shouldFilterProcessModel(item, search) && !('process_groups' in item)
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
      setCurrentProcessGroup(null);
      treeRef.current?.clearExpanded();
      navigate('/process-groups');
      return;
    }
    // Otherwise, find the item in the flatItems list and feed it to the clickstream.
    const found = flatItems.find((item: any) => item.id === crumb.id);
    if (found) {
      clickStream.next(found);
      const processEntityId = modifyProcessIdentifierForPathParam(crumb.id);
      setCurrentProcessGroup(found);
      navigate(`/process-groups/${processEntityId}`);
    }
  };

  const dataStoresForProcessGroup = dataStores.filter(
    (dataStore: DataStore) => {
      return (
        currentProcessGroup && dataStore.location === currentProcessGroup.id
      );
    },
  );

  const deleteProcessGroup = () => {
    if (currentProcessGroup) {
      const modifiedGroupId = modifyProcessIdentifierForPathParam(
        currentProcessGroup.id,
      );
      let parendGroupId = modifiedGroupId.replace(/:[^:]+$/, '');
      // this means it was a root group
      if (parendGroupId === modifiedGroupId) {
        parendGroupId = SPIFF_ID;
      }
      HttpService.makeCallToBackend({
        path: `/process-groups/${modifiedGroupId}`,
        successCallback: () => {
          handleCrumbClick({
            id: parendGroupId.replaceAll(':', '/'),
            displayName: 'NOT_USED',
          });
        },
        httpMethod: 'DELETE',
      });
    }
  };

  const currentParentGroupIdSearchParam = () => {
    return currentProcessGroup
      ? `?parentGroupId=${currentProcessGroup.id}`
      : '';
  };

  return (
    <Box id="process-model-tree-box" sx={{ margin: '0 auto', p: 0 }}>
      <Typography variant="h1" sx={{ mb: 2 }}>
        Processes
      </Typography>
      <Container
        maxWidth={false}
        sx={{
          padding: '0px !important',
          height: '100%',
        }}
        id="list-container"
      >
        <Stack
          id="process-model-tree-stack"
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
            </Stack>
            <Card>
              <CardContent>
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    mb: 3,
                    width: '100%',
                  }}
                >
                  {currentProcessGroup ? (
                    <>
                      <Breadcrumbs sx={{ mb: 3 }}>
                        <Button
                          sx={{ display: 'flex', alignItems: 'center' }}
                          onClick={(e: React.MouseEvent<HTMLButtonElement>) => {
                            e.preventDefault();
                            handleCrumbClick({
                              id: SPIFF_ID,
                              displayName: 'Home',
                            });
                          }}
                        >
                          <Home sx={{ mr: 0.5 }} fontSize="inherit" />
                          Root
                        </Button>
                        {crumbs.map((crumb) => (
                          <Link
                            key={crumb.id}
                            href={`/process-groups/${modifyProcessIdentifierForPathParam(crumb.id)}`}
                            onClick={(
                              e: React.MouseEvent<HTMLAnchorElement>,
                            ) => {
                              e.preventDefault();
                              handleCrumbClick(crumb);
                            }}
                          >
                            {crumb.displayName}
                          </Link>
                        ))}
                      </Breadcrumbs>
                      <Box>
                        <Can
                          I="PUT"
                          a={targetUris.processGroupShowPath}
                          ability={ability}
                        >
                          <IconButton
                            data-qa="edit-process-group-button"
                            href={`/process-groups/${modifyProcessIdentifierForPathParam(currentProcessGroup.id)}/edit`}
                          >
                            <Edit />
                          </IconButton>
                        </Can>
                        <Can
                          I="DELETE"
                          a={targetUris.processGroupShowPath}
                          ability={ability}
                        >
                          <ButtonWithConfirmation
                            data-qa="delete-process-group-button"
                            renderIcon={<Delete />}
                            iconDescription="Delete Process Group"
                            hasIconOnly
                            description={`Delete process group: ${currentProcessGroup.display_name}`}
                            onConfirmation={deleteProcessGroup}
                            confirmButtonLabel="Delete"
                          />
                        </Can>
                      </Box>
                    </>
                  ) : (
                    <Breadcrumbs sx={{ mb: 3 }}>
                      <Button
                        sx={{ display: 'flex', alignItems: 'center' }}
                        onClick={(e: React.MouseEvent<HTMLButtonElement>) => {
                          e.preventDefault();
                          handleCrumbClick({
                            id: SPIFF_ID,
                            displayName: 'Home',
                          });
                        }}
                      >
                        <Home sx={{ mr: 0.5 }} fontSize="inherit" />
                        Root
                      </Button>
                    </Breadcrumbs>
                  )}
                </Box>
                {currentProcessGroup && (
                  <Stack
                    direction="row"
                    sx={{
                      width: '100%',
                      paddingBottom: 2,
                    }}
                  >
                    {currentProcessGroup.description}
                  </Stack>
                )}
                <Accordion
                  expanded={modelsExpanded}
                  onChange={() => setModelsExpanded((prev) => !prev)}
                >
                  <AccordionSummary
                    expandIcon={<ExpandMoreIcon />}
                    aria-controls="Process Models Accordion"
                  >
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        width: '100%',
                        pr: 2,
                      }}
                    >
                      <Typography>Process Models ({models.length})</Typography>
                      {currentProcessGroup && (
                        <Can
                          I="POST"
                          a={targetUris.processModelCreatePath}
                          ability={ability}
                        >
                          <IconButton
                            size="small"
                            onClick={(e) => e.stopPropagation()}
                            data-qa="add-process-model-button"
                            href={`/process-models/${modifyProcessIdentifierForPathParam(currentProcessGroup.id)}/new`}
                          >
                            <Add />
                          </IconButton>
                        </Can>
                      )}
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box sx={gridProps}>
                      {models.map((model: ProcessModel) => (
                        <ProcessModelCard
                          key={model.id}
                          model={model}
                          stream={clickStream}
                          lastSelected={currentProcessGroup || {}}
                          onStartProcess={() => {
                            if (setNavElementCallback) {
                              // remove the TreePanel from the SideNav when starting a process
                              setNavElementCallback(null);
                            }
                          }}
                          onViewProcess={() => {
                            if (setNavElementCallback) {
                              setNavElementCallback(null);
                            }
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
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        width: '100%',
                        pr: 2,
                      }}
                    >
                      <Typography>Process Groups ({groups?.length})</Typography>
                      <Can
                        I="POST"
                        a={targetUris.processGroupListPath}
                        ability={ability}
                      >
                        <IconButton
                          size="small"
                          onClick={(e) => e.stopPropagation()}
                          data-qa="add-process-group-button"
                          href={`/process-groups/new${currentParentGroupIdSearchParam()}`}
                        >
                          <Add />
                        </IconButton>
                      </Can>
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box sx={gridProps}>
                      {groups?.map((group: Record<string, any>) => (
                        <ProcessGroupCard
                          key={group.id}
                          group={group}
                          stream={clickStream}
                          navigateToPage={navigateToPage}
                        />
                      ))}
                    </Box>
                  </AccordionDetails>
                </Accordion>
                <Can I="GET" a={targetUris.dataStoreListPath} ability={ability}>
                  <Accordion
                    expanded={dataStoreExpanded}
                    onChange={() => setDataStoreExpanded((prev) => !prev)}
                  >
                    <AccordionSummary
                      expandIcon={<ExpandMoreIcon />}
                      aria-controls="Data Store Accordion"
                    >
                      <Box
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          width: '100%',
                          pr: 2,
                        }}
                      >
                        <Typography>
                          Data Stores ({dataStoresForProcessGroup?.length})
                        </Typography>
                        <IconButton
                          size="small"
                          onClick={(e) => e.stopPropagation()}
                          data-qa="add-process-group-button"
                          href={`/data-stores/new${currentParentGroupIdSearchParam()}`}
                        >
                          <Add />
                        </IconButton>
                      </Box>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Box sx={gridProps}>
                        {dataStoresForProcessGroup?.map(
                          (dataStore: DataStore) => (
                            <DataStoreCard dataStore={dataStore} />
                          ),
                        )}
                      </Box>
                    </AccordionDetails>
                  </Accordion>
                </Can>
              </CardContent>
            </Card>
          </Stack>
        </Stack>
      </Container>
    </Box>
  );
}
