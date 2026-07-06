import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Chip,
  Container,
  Divider,
  IconButton,
  Stack,
  Typography,
  Breadcrumbs,
  Link,
  ListItemIcon,
  ListSubheader,
  ListItemText,
  Card,
  CardContent,
  Button,
  Menu,
  MenuItem,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import React, {
  ReactNode,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import { Can } from '@casl/react';
import { Subject } from 'rxjs';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import StarRateIcon from '@mui/icons-material/StarRate';
import {
  Delete,
  Edit,
  Add,
  Folder,
  Home,
  MoreVert,
  PlayArrow,
  ViewList,
  ViewModule,
} from '@mui/icons-material';
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
  ProcessModelSortOption,
  ProcessModelStatsMap,
} from '../../interfaces';
import {
  modifyProcessIdentifierForPathParam,
  unModifyProcessIdentifierForPathParam,
} from '../../helpers';
import { useUriListForPermissions } from '../../hooks/UriListForPermissions';
import { usePermissionFetcher } from '../../hooks/PermissionService';
import ConfirmIconButton from '../../components/ConfirmIconButton';
import HttpService from '../../services/HttpService';
import DataStoreCard from '../../components/DataStoreCard';
import CollapsibleGroupTree, {
  ModelRowContext,
} from '../../components/processGroupTree/CollapsibleGroupTree';
import {
  buildGroupInstanceCountMap,
  buildGroupModelCountMap,
  filterProcessGroupTree,
} from '../../components/processGroupTree/groupTreeHelpers';
import { useConfirmationDialog } from '../../hooks/useConfirmationDialog';

const SPIFF_ID = 'spifftop';
type Crumb = { id: string; displayName: string };
type ViewMode = 'list' | 'cards';

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

function ProcessModelTreeControls({
  clickStream,
  handleSearch,
  onShowOnlyRunChange,
  onSortChange,
  onViewModeChange,
  showOnlyRun,
  sortBy,
  viewMode,
}: {
  clickStream: Subject<Record<string, any>>;
  handleSearch: (search: string) => void;
  onShowOnlyRunChange: (checked: boolean) => void;
  onSortChange: (sort: ProcessModelSortOption) => void;
  onViewModeChange: (viewMode: ViewMode) => void;
  showOnlyRun: boolean;
  sortBy: ProcessModelSortOption;
  viewMode: ViewMode;
}) {
  const { t } = useTranslation();

  return (
    <Stack
      direction={{ xs: 'column', sm: 'row' }}
      gap={1}
      sx={{
        width: '100%',
        paddingTop: 2,
        justifyContent: 'center',
        alignItems: { xs: 'stretch', sm: 'center' },
      }}
    >
      <SearchBar
        callback={handleSearch}
        stream={clickStream}
        sortBy={sortBy}
        onSortChange={onSortChange}
        showOnlyRun={showOnlyRun}
        onShowOnlyRunChange={onShowOnlyRunChange}
      />
      <ToggleButtonGroup
        size="small"
        exclusive
        value={viewMode}
        onChange={(_e, value) => {
          if (value) {
            onViewModeChange(value);
          }
        }}
        aria-label={t('view_mode')}
        sx={{ alignSelf: { xs: 'flex-end', sm: 'center' } }}
      >
        <ToggleButton
          value="list"
          aria-label={t('view_nested_list')}
          title={t('view_nested_list')}
        >
          <ViewList fontSize="small" />
        </ToggleButton>
        <ToggleButton
          value="cards"
          aria-label={t('view_cards')}
          title={t('view_cards')}
        >
          <ViewModule fontSize="small" />
        </ToggleButton>
      </ToggleButtonGroup>
    </Stack>
  );
}

function FavoritesShortcut({
  onClick,
  treeCollapsed,
}: {
  onClick: () => void;
  treeCollapsed: boolean;
}) {
  const { t } = useTranslation();

  if (!treeCollapsed) {
    return null;
  }

  return (
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
      onClick={onClick}
    >
      <StarRateIcon
        sx={{
          transform: 'scale(.8)',
          color: 'spotColors.goldStar',
          position: 'relative',
          top: -1,
        }}
      />
      <Typography variant="caption">{t('favorites')}</Typography>
    </Stack>
  );
}

function CatalogAccordion({
  action,
  ariaControls,
  children,
  expanded,
  onToggle,
  title,
}: {
  action?: ReactNode;
  ariaControls: string;
  children: ReactNode;
  expanded: boolean;
  onToggle: () => void;
  title: ReactNode;
}) {
  return (
    <Accordion expanded={expanded} onChange={() => onToggle()}>
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        aria-controls={ariaControls}
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
          <Typography>{title}</Typography>
          {action}
        </Box>
      </AccordionSummary>
      <AccordionDetails>{children}</AccordionDetails>
    </Accordion>
  );
}

function ProcessGroupHeader({
  ability,
  crumbs,
  currentProcessGroup,
  deleteProcessGroup,
  handleCrumbClick,
  compact = false,
  targetUris,
}: {
  ability: any;
  crumbs: Crumb[];
  currentProcessGroup: Record<string, any> | null;
  deleteProcessGroup: () => void;
  handleCrumbClick: (crumb: Crumb) => void;
  compact?: boolean;
  targetUris: ReturnType<typeof useUriListForPermissions>['targetUris'];
}) {
  const { t } = useTranslation();

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        mb: compact ? 1 : 3,
        p: compact ? 2 : 0,
        pb: compact ? 1 : 0,
        width: '100%',
      }}
    >
      <Breadcrumbs sx={{ mb: compact ? 0 : 3 }}>
        <Button
          sx={{ display: 'flex', alignItems: 'center' }}
          onClick={(e: React.MouseEvent<HTMLButtonElement>) => {
            e.preventDefault();
            handleCrumbClick({
              id: SPIFF_ID,
              displayName: t('home'),
            });
          }}
        >
          <Home sx={{ mr: 0.5 }} fontSize="inherit" />
          Root
        </Button>
        {currentProcessGroup
          ? crumbs.map((crumb) => (
              <Link
                key={crumb.id}
                href={`/process-groups/${modifyProcessIdentifierForPathParam(crumb.id)}`}
                data-testid={`process-group-breadcrumb-${crumb.displayName}`}
                onClick={(e: React.MouseEvent<HTMLAnchorElement>) => {
                  e.preventDefault();
                  handleCrumbClick(crumb);
                }}
              >
                {crumb.displayName}
              </Link>
            ))
          : null}
      </Breadcrumbs>
      {currentProcessGroup ? (
        <Box>
          <Can I="PUT" a={targetUris.processGroupShowPath} ability={ability}>
            <IconButton
              data-testid="edit-process-group-button"
              href={`/process-groups/${modifyProcessIdentifierForPathParam(currentProcessGroup.id)}/edit`}
            >
              <Edit />
            </IconButton>
          </Can>
          <Can I="DELETE" a={targetUris.processGroupShowPath} ability={ability}>
            <ConfirmIconButton
              data-testid="delete-process-group-button"
              renderIcon={<Delete />}
              iconDescription={t('delete_process_group')}
              description={t('delete_process_group_with_name', {
                name: currentProcessGroup.display_name,
              })}
              onConfirmation={deleteProcessGroup}
              confirmButtonLabel={t('delete')}
            />
          </Can>
        </Box>
      ) : null}
    </Box>
  );
}

function GroupRowActions({
  ability,
  currentProcessGroupId,
  group,
  onAddChildGroup,
  onAddProcessModel,
  onDeleteGroup,
  onOpenGroup,
}: {
  ability: any;
  currentProcessGroupId?: string;
  group: ProcessGroup;
  onAddChildGroup: (groupId: string) => void;
  onAddProcessModel: (groupId: string) => void;
  onDeleteGroup: (group: ProcessGroup) => void;
  onOpenGroup: (groupId: string) => void;
}) {
  const { t } = useTranslation();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const modifiedGroupId = modifyProcessIdentifierForPathParam(group.id);
  const {
    openConfirmation: openDeleteConfirmation,
    ConfirmationDialog: DeleteConfirmationDialog,
  } = useConfirmationDialog(() => onDeleteGroup(group), {
    description: t('delete_process_group_with_name', {
      name: group.display_name,
    }),
    confirmText: t('delete'),
    confirmColor: 'error',
  });

  const closeMenu = () => setAnchorEl(null);
  const editProcessGroupLabel = `${t('edit')} ${t('process_group')}`;
  const isCurrentProcessGroup = group.id === currentProcessGroupId;

  return (
    <>
      <IconButton
        size="small"
        title={t('more_actions')}
        data-testid={`process-group-actions-button-${modifiedGroupId}`}
        onClick={(e) => {
          e.stopPropagation();
          setAnchorEl(e.currentTarget);
        }}
      >
        <MoreVert fontSize="small" />
      </IconButton>
      <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={closeMenu}>
        {isCurrentProcessGroup ? null : (
          <>
            <MenuItem
              data-testid={`open-process-group-menu-item-${modifiedGroupId}`}
              onClick={() => {
                closeMenu();
                onOpenGroup(group.id);
              }}
            >
              <ListItemIcon>
                <Folder fontSize="small" />
              </ListItemIcon>
              <ListItemText>{t('open_process_group')}</ListItemText>
            </MenuItem>
            <Divider />
          </>
        )}
        <ListSubheader>{t('add_inside_this_group')}</ListSubheader>
        <Can I="POST" a="/v1.0/process-groups" ability={ability}>
          <MenuItem
            data-testid={`add-child-process-group-menu-item-${modifiedGroupId}`}
            onClick={() => {
              closeMenu();
              onAddChildGroup(group.id);
            }}
          >
            <ListItemIcon>
              <Add fontSize="small" />
            </ListItemIcon>
            <ListItemText>{t('process_group')}</ListItemText>
            <ListItemIcon sx={{ minWidth: 0, ml: 2 }}>
              <Folder fontSize="small" />
            </ListItemIcon>
          </MenuItem>
        </Can>
        <Can
          I="POST"
          a={`/v1.0/process-models/${modifiedGroupId}`}
          ability={ability}
        >
          <MenuItem
            data-testid={`add-process-model-menu-item-${modifiedGroupId}`}
            onClick={() => {
              closeMenu();
              onAddProcessModel(group.id);
            }}
          >
            <ListItemIcon>
              <Add fontSize="small" />
            </ListItemIcon>
            <ListItemText>{t('process_model')}</ListItemText>
          </MenuItem>
        </Can>
        <Divider />
        <Can
          I="PUT"
          a={`/v1.0/process-groups/${modifiedGroupId}`}
          ability={ability}
        >
          <MenuItem
            component="a"
            href={`/process-groups/${modifiedGroupId}/edit`}
            data-testid={`edit-process-group-menu-item-${modifiedGroupId}`}
            onClick={closeMenu}
          >
            <ListItemIcon>
              <Edit fontSize="small" />
            </ListItemIcon>
            <ListItemText>{editProcessGroupLabel}</ListItemText>
          </MenuItem>
        </Can>
        <Can
          I="DELETE"
          a={`/v1.0/process-groups/${modifiedGroupId}`}
          ability={ability}
        >
          <MenuItem
            data-testid={`delete-process-group-menu-item-${modifiedGroupId}`}
            onClick={() => {
              closeMenu();
              openDeleteConfirmation();
            }}
          >
            <ListItemIcon>
              <Delete fontSize="small" />
            </ListItemIcon>
            <ListItemText>{t('delete_process_group')}</ListItemText>
          </MenuItem>
        </Can>
      </Menu>
      <DeleteConfirmationDialog />
    </>
  );
}

function ModelRowActions({
  ability,
  model,
  onDeleteModel,
}: {
  ability: any;
  model: ProcessModel;
  onDeleteModel: (model: ProcessModel) => void;
}) {
  const { t } = useTranslation();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const modifiedModelId = modifyProcessIdentifierForPathParam(model.id);
  const {
    openConfirmation: openDeleteConfirmation,
    ConfirmationDialog: DeleteConfirmationDialog,
  } = useConfirmationDialog(() => onDeleteModel(model), {
    description: t('delete_process_model_confirm', {
      processModelName: model.display_name,
    }),
    confirmText: t('delete'),
    confirmColor: 'error',
  });

  const closeMenu = () => setAnchorEl(null);

  return (
    <>
      <IconButton
        size="small"
        title={t('more_actions')}
        data-testid={`process-model-actions-button-${modifiedModelId}`}
        onClick={(e) => {
          e.stopPropagation();
          setAnchorEl(e.currentTarget);
        }}
      >
        <MoreVert fontSize="small" />
      </IconButton>
      <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={closeMenu}>
        <Can
          I="PUT"
          a={`/v1.0/process-models/${modifiedModelId}`}
          ability={ability}
        >
          <MenuItem
            component="a"
            href={`/process-models/${modifiedModelId}/edit`}
            data-testid={`edit-process-model-menu-item-${modifiedModelId}`}
            onClick={closeMenu}
          >
            <ListItemIcon>
              <Edit fontSize="small" />
            </ListItemIcon>
            <ListItemText>{t('edit_process_model')}</ListItemText>
          </MenuItem>
        </Can>
        <Can
          I="DELETE"
          a={`/v1.0/process-models/${modifiedModelId}`}
          ability={ability}
        >
          <MenuItem
            data-testid={`delete-process-model-menu-item-${modifiedModelId}`}
            onClick={() => {
              closeMenu();
              openDeleteConfirmation();
            }}
          >
            <ListItemIcon>
              <Delete fontSize="small" />
            </ListItemIcon>
            <ListItemText>{t('delete_process_model')}</ListItemText>
          </MenuItem>
        </Can>
      </Menu>
      <DeleteConfirmationDialog />
    </>
  );
}

/**
 * Top level layout and control container for this view,
 * feeds various streams, data and callbacks to children.
 */
export default function ProcessModelTreePage({
  setNavElementCallback,
  navigateToPage = false,
}: OwnProps) {
  const { t } = useTranslation();
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
  const [sortBy, setSortBy] = useState<ProcessModelSortOption>('alphabetical');
  const [showOnlyRun, setShowOnlyRun] = useState(false);
  const [modelStats, setModelStats] = useState<ProcessModelStatsMap>({});
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [searchText, setSearchText] = useState('');
  const [processGroupNotFound, setProcessGroupNotFound] = useState(false);
  const treeRef = useRef<TreeRef>(null);
  // Use useRef to maintain a stable stream instance across re-renders
  const clickStream = useRef(new Subject<Record<string, any>>()).current;
  const favoriteCrumb: Crumb = { id: 'favorites', displayName: t('favorites') };
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
  const permissionRequestData: PermissionsToCheck = useMemo(() => {
    const requests: PermissionsToCheck = {
      [targetUris.dataStoreListPath]: ['GET'],
      [targetUris.processGroupListPath]: ['POST'],
      [targetUris.processGroupShowPath]: ['PUT', 'DELETE'],
      [targetUris.processModelCreatePath]: ['POST'],
    };

    const addGroupPermissions = (group: ProcessGroup | ProcessGroupLite) => {
      const modifiedGroupId = modifyProcessIdentifierForPathParam(group.id);
      requests[`/v1.0/process-groups/${modifiedGroupId}`] = ['PUT', 'DELETE'];
      requests[`/v1.0/process-models/${modifiedGroupId}`] = ['POST'];
      (group.process_models || []).forEach((model: ProcessModel) => {
        requests[
          `/v1.0/process-models/${modifyProcessIdentifierForPathParam(model.id)}`
        ] = ['PUT', 'DELETE'];
      });
      (group.process_groups || []).forEach(addGroupPermissions);
    };

    ((processGroups as ProcessGroup[]) || []).forEach(addGroupPermissions);
    return requests;
  }, [
    processGroups,
    targetUris.dataStoreListPath,
    targetUris.processGroupListPath,
    targetUris.processGroupShowPath,
    targetUris.processModelCreatePath,
  ]);
  const { ability, permissionsLoaded } = usePermissionFetcher(
    permissionRequestData,
  );

  useEffect(() => {
    HttpService.makeCallToBackend({
      path: '/process-models/stats',
      successCallback: (result: ProcessModelStatsMap) => {
        setModelStats(result);
      },
      onUnauthorized: () => setModelStats({}),
    });
  }, []);

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
  const requestedProcessGroupId =
    params.process_group_id && params.process_group_id !== 'undefined'
      ? unModifyProcessIdentifierForPathParam(`${params.process_group_id}`)
      : null;

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
      const processGroupsLite: ProcessGroupLite[] =
        processGroups.map(processGroupToLite);
      const foundProcessGroup = findProcessGroupByPath(
        processGroupsLite,
        requestedProcessGroupId || '',
      );
      if (foundProcessGroup) {
        setGroups(foundProcessGroup.process_groups || null);
        setModels(foundProcessGroup.process_models || []);
        setCrumbs(processCrumbs(foundProcessGroup, flattened));
        setCurrentProcessGroup(foundProcessGroup);
        setProcessGroupNotFound(false);
      } else {
        setGroups(processGroupsLite);
        setCrumbs([]);
        setCurrentProcessGroup(null);
        setProcessGroupNotFound(!!requestedProcessGroupId);
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

  const sortAndFilterModels = useCallback(
    (items: ProcessModel[]): ProcessModel[] => {
      let result = [...items];
      if (showOnlyRun) {
        result = result.filter((m) => modelStats[m.id]?.instance_count > 0);
      }
      result.sort((a, b) => {
        if (sortBy === 'recently_ran') {
          const aTime = modelStats[a.id]?.last_run_in_seconds ?? 0;
          const bTime = modelStats[b.id]?.last_run_in_seconds ?? 0;
          return bTime - aTime;
        }
        if (sortBy === 'most_used') {
          const aCount = modelStats[a.id]?.instance_count ?? 0;
          const bCount = modelStats[b.id]?.instance_count ?? 0;
          return bCount - aCount;
        }
        return a.display_name.localeCompare(b.display_name);
      });
      return result;
    },
    [sortBy, showOnlyRun, modelStats],
  );

  const displayedModels = useMemo(
    () => sortAndFilterModels(models),
    [models, sortAndFilterModels],
  );

  const handleSearch = useDebouncedCallback((search: string) => {
    // Drive the nested-list view's tree filtering.
    setSearchText(search);
    // Indicate to user this is a search result.
    setCrumbs([
      { id: search, displayName: `${t('search')}: ${search || '(all)'}` },
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
      setProcessGroupNotFound(false);
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
      setProcessGroupNotFound(false);
      navigate(`/process-groups/${processEntityId}`);
    }
  };

  const dataStoresForProcessGroup = dataStores.filter(
    (dataStore: DataStore) => {
      return (
        (currentProcessGroup &&
          dataStore.location === currentProcessGroup.id) ||
        (!currentProcessGroup &&
          (!dataStore.location || dataStore.location === '/'))
      );
    },
  );

  const parentProcessGroupId = (groupId: string): string | null => {
    const modifiedGroupId = modifyProcessIdentifierForPathParam(groupId);
    const modifiedParentGroupId = modifiedGroupId.replace(/:[^:]+$/, '');
    if (modifiedParentGroupId === modifiedGroupId) {
      return null;
    }
    return modifiedParentGroupId.replaceAll(':', '/');
  };

  const processGroupPath = (groupId: string | null) => {
    return groupId
      ? `/process-groups/${modifyProcessIdentifierForPathParam(groupId)}`
      : '/process-groups';
  };

  const goToParentAfterProcessGroupDelete = (groupId: string) => {
    window.location.href = processGroupPath(parentProcessGroupId(groupId));
  };

  const deleteProcessGroup = () => {
    if (currentProcessGroup) {
      const modifiedGroupId = modifyProcessIdentifierForPathParam(
        currentProcessGroup.id,
      );
      HttpService.makeCallToBackend({
        path: `/process-groups/${modifiedGroupId}`,
        successCallback: () =>
          goToParentAfterProcessGroupDelete(currentProcessGroup.id),
        httpMethod: 'DELETE',
      });
    }
  };

  const deleteProcessGroupFromList = (group: ProcessGroup) => {
    HttpService.makeCallToBackend({
      path: `/process-groups/${modifyProcessIdentifierForPathParam(group.id)}`,
      successCallback: () => {
        if (group.id === currentProcessGroup?.id) {
          goToParentAfterProcessGroupDelete(group.id);
        } else {
          window.location.reload();
        }
      },
      httpMethod: 'DELETE',
    });
  };

  const deleteProcessModelFromList = (model: ProcessModel) => {
    HttpService.makeCallToBackend({
      path: `/process-models/${modifyProcessIdentifierForPathParam(model.id)}`,
      successCallback: () => window.location.reload(),
      httpMethod: 'DELETE',
    });
  };

  const currentParentGroupIdSearchParam = () => {
    return currentProcessGroup
      ? `?parentGroupId=${encodeURIComponent(currentProcessGroup.id)}`
      : '';
  };

  const newProcessGroupPath = () => {
    return `/process-groups/new${currentParentGroupIdSearchParam()}`;
  };

  const newProcessModelPath = (groupId: string) => {
    return `/process-models/${modifyProcessIdentifierForPathParam(groupId)}/new`;
  };

  const navigateToNewChildProcessGroup = (groupId: string) => {
    navigate(
      `/process-groups/new?parentGroupId=${encodeURIComponent(groupId)}`,
    );
  };

  const navigateToNewProcessModelInGroup = (groupId: string) => {
    navigate(newProcessModelPath(groupId));
  };
  const navigateToFocusedProcessGroup = (groupId: string) => {
    const found = flatItems.find(
      (item: any) => item.id === groupId && 'process_groups' in item,
    );
    if (found) {
      clickStream.next(found);
      return;
    }
    navigate(`/process-groups/${modifyProcessIdentifierForPathParam(groupId)}`);
  };

  // ---- Nested collapsible list view (Odoo-style) ----
  const groupInstanceCountMap = useMemo(
    () => buildGroupInstanceCountMap(modelStats),
    [modelStats],
  );
  const groupModelCountMap = useMemo(
    () => buildGroupModelCountMap((processGroups as ProcessGroup[]) || []),
    [processGroups],
  );
  const treeRootGroups = useMemo(
    () =>
      currentProcessGroup
        ? ([currentProcessGroup] as ProcessGroup[])
        : (processGroups as ProcessGroup[]) || [],
    [currentProcessGroup, processGroups],
  );
  const treeGroupsToDisplay = useMemo(
    () => filterProcessGroupTree(treeRootGroups, searchText),
    [treeRootGroups, searchText],
  );
  const collectGroupIds = useCallback((groupList: ProcessGroup[]): string[] => {
    const ids: string[] = [];
    const walk = (group: ProcessGroup) => {
      ids.push(group.id);
      (group.process_groups || []).forEach(walk);
    };
    groupList.forEach(walk);
    return ids;
  }, []);
  // While searching, expand every matching group so results are visible.
  const treeExpandedIds = searchText
    ? collectGroupIds(treeGroupsToDisplay)
    : currentProcessGroup
      ? [currentProcessGroup.id]
      : [];

  const navigateToViewModel = (model: ProcessModel) => {
    if (setNavElementCallback) {
      setNavElementCallback(null);
    }
    navigate(
      `/process-models/${modifyProcessIdentifierForPathParam(model.id)}`,
    );
  };
  const navigateToStartModel = (model: ProcessModel) => {
    if (setNavElementCallback) {
      setNavElementCallback(null);
    }
    navigate(`/${modifyProcessIdentifierForPathParam(model.id)}/start`);
  };

  const renderCatalogModelRow = (model: ProcessModel, ctx: ModelRowContext) => {
    const stats = modelStats[model.id];
    return (
      <Box
        key={model.id}
        role="button"
        tabIndex={0}
        data-testid={`group-tree-model-${modifyProcessIdentifierForPathParam(model.id)}`}
        onClick={() => navigateToViewModel(model)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            navigateToViewModel(model);
          }
        }}
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          cursor: 'pointer',
          py: 0.75,
          pl: ctx.depth * 2.5 + 3,
          pr: 2,
          borderBottom: '1px solid',
          borderColor: 'borders.primary',
          backgroundColor: 'background.paper',
          '&:hover': { backgroundColor: 'action.hover' },
        }}
      >
        <Box sx={{ minWidth: 0 }}>
          <Typography variant="body2" sx={{ fontWeight: 500 }} noWrap>
            {model.display_name}
          </Typography>
          {model.description ? (
            <Typography variant="caption" color="text.secondary" noWrap>
              {model.description}
            </Typography>
          ) : null}
        </Box>
        <Box sx={{ flexGrow: 1 }} />
        {stats && stats.instance_count > 0 ? (
          <Typography variant="caption" color="text.disabled">
            {t('n_runs', { count: stats.instance_count })}
          </Typography>
        ) : null}
        <Tooltip title={t('start_process')}>
          <IconButton
            color="primary"
            size="small"
            aria-label={t('start_process')}
            onClick={(e) => {
              e.stopPropagation();
              navigateToStartModel(model);
            }}
            sx={{ display: { xs: 'inline-flex', sm: 'none' } }}
          >
            <PlayArrow fontSize="small" />
          </IconButton>
        </Tooltip>
        <Button
          variant="contained"
          size="small"
          onClick={(e) => {
            e.stopPropagation();
            navigateToStartModel(model);
          }}
          sx={{ display: { xs: 'none', sm: 'inline-flex' } }}
        >
          {t('start_process')}
        </Button>
        <ModelRowActions
          ability={ability}
          model={model}
          onDeleteModel={deleteProcessModelFromList}
        />
      </Box>
    );
  };

  const renderNestedListView = () => (
    <Card>
      <CardContent sx={{ p: 0 }}>
        {currentProcessGroup ? (
          <ProcessGroupHeader
            ability={ability}
            compact
            crumbs={crumbs}
            currentProcessGroup={currentProcessGroup}
            deleteProcessGroup={deleteProcessGroup}
            handleCrumbClick={handleCrumbClick}
            targetUris={targetUris}
          />
        ) : null}
        <CollapsibleGroupTree
          key={`tree-${currentProcessGroup?.id ?? 'root'}-${searchText}`}
          processGroups={treeGroupsToDisplay}
          renderModelRow={renderCatalogModelRow}
          getGroupInstanceCount={(id) => groupInstanceCountMap[id] ?? 0}
          getModelInstanceCount={(id) => modelStats[id]?.instance_count ?? 0}
          sortProcessModels={sortAndFilterModels}
          showEmptyGroupsAndModels={!showOnlyRun}
          defaultExpandedGroupIds={treeExpandedIds}
          emptyText={t('no_results')}
          renderGroupActions={(group) => (
            <GroupRowActions
              ability={ability}
              currentProcessGroupId={currentProcessGroup?.id}
              group={group}
              onAddChildGroup={navigateToNewChildProcessGroup}
              onAddProcessModel={navigateToNewProcessModelInGroup}
              onDeleteGroup={deleteProcessGroupFromList}
              onOpenGroup={navigateToFocusedProcessGroup}
            />
          )}
          renderGroupMetadata={(group, count) => (
            <Stack direction="row" gap={1} alignItems="center">
              {count > 0 ? (
                <Chip
                  size="small"
                  label={t('n_runs', { count })}
                  sx={{ display: { xs: 'none', sm: 'inline-flex' } }}
                />
              ) : null}
              <Chip
                size="small"
                variant="outlined"
                label={t('n_models', {
                  count: groupModelCountMap[group.id] ?? 0,
                })}
              />
            </Stack>
          )}
        />
      </CardContent>
    </Card>
  );

  return (
    <Box id="process-model-tree-box" sx={{ margin: '0 auto', p: 0 }}>
      <Stack
        direction={{ xs: 'column', sm: 'row' }}
        justifyContent="space-between"
        alignItems={{ xs: 'stretch', sm: 'center' }}
        gap={1}
        sx={{ mb: 2 }}
      >
        <Typography variant="h1">{t('processes')}</Typography>
        {processGroupNotFound ? null : (
          <Stack direction="row" gap={1} justifyContent="flex-end">
            <Can I="POST" a={targetUris.processGroupListPath} ability={ability}>
              <Button
                variant="outlined"
                size="small"
                startIcon={<Add />}
                data-testid="add-process-group-button"
                href={newProcessGroupPath()}
              >
                {t('add_process_group')}
              </Button>
            </Can>
          </Stack>
        )}
      </Stack>
      {processGroupNotFound ? (
        <Card>
          <CardContent>
            <Stack gap={2} alignItems="flex-start">
              <Typography variant="h2">
                {t('process_group_not_found_title')}
              </Typography>
              <Typography variant="body1" color="text.secondary">
                {t('process_group_not_found_message', {
                  groupId: requestedProcessGroupId,
                })}
              </Typography>
              <Button variant="contained" href="/process-groups">
                {t('back_to_process_groups')}
              </Button>
            </Stack>
          </CardContent>
        </Card>
      ) : (
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
            <ProcessModelTreeControls
              clickStream={clickStream}
              handleSearch={handleSearch}
              onShowOnlyRunChange={setShowOnlyRun}
              onSortChange={setSortBy}
              onViewModeChange={setViewMode}
              showOnlyRun={showOnlyRun}
              sortBy={sortBy}
              viewMode={viewMode}
            />

            <Stack
              sx={{
                width: '100%',
                overflowY: 'auto',
                overflowX: 'hidden',
              }}
              id="scrollable-process-card-area"
            >
              <Stack direction="row" gap={1} sx={{ paddingBottom: 0.5 }}>
                <FavoritesShortcut
                  treeCollapsed={treeCollapsed}
                  onClick={() => handleFavorites({ text: SHOW_FAVORITES })}
                />
              </Stack>
              {viewMode === 'list' ? (
                renderNestedListView()
              ) : (
                <Card>
                  <CardContent>
                    <ProcessGroupHeader
                      ability={ability}
                      crumbs={crumbs}
                      currentProcessGroup={currentProcessGroup}
                      deleteProcessGroup={deleteProcessGroup}
                      handleCrumbClick={handleCrumbClick}
                      targetUris={targetUris}
                    />
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
                    <CatalogAccordion
                      ariaControls="Process Models Accordion"
                      expanded={modelsExpanded}
                      onToggle={() => setModelsExpanded((prev) => !prev)}
                      title={t('process_models_with_count', {
                        count: displayedModels.length,
                      })}
                      action={
                        currentProcessGroup ? (
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            <Can
                              I="POST"
                              a={targetUris.processModelCreatePath}
                              ability={ability}
                            >
                              <IconButton
                                size="small"
                                onClick={(e) => e.stopPropagation()}
                                href={`/process-models/${modifyProcessIdentifierForPathParam(currentProcessGroup.id)}/new`}
                              >
                                <Add />
                              </IconButton>
                            </Can>
                          </Box>
                        ) : null
                      }
                    >
                      <Box sx={gridProps}>
                        {displayedModels.map((model: ProcessModel) => (
                          <ProcessModelCard
                            key={model.id}
                            model={model}
                            stream={clickStream}
                            lastSelected={currentProcessGroup || {}}
                            stats={modelStats[model.id]}
                            onStartProcess={() => {
                              if (setNavElementCallback) {
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
                    </CatalogAccordion>
                    <CatalogAccordion
                      ariaControls="Process Groups Accordion"
                      expanded={groupsExpanded}
                      onToggle={() => setGroupsExpanded((prev) => !prev)}
                      title={`${t('process_groups')} (${groups?.length})`}
                      action={
                        <Can
                          I="POST"
                          a={targetUris.processGroupListPath}
                          ability={ability}
                        >
                          <IconButton
                            size="small"
                            onClick={(e) => e.stopPropagation()}
                            href={`/process-groups/new${currentParentGroupIdSearchParam()}`}
                          >
                            <Add />
                          </IconButton>
                        </Can>
                      }
                    >
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
                    </CatalogAccordion>
                    <Can
                      I="GET"
                      a={targetUris.dataStoreListPath}
                      ability={ability}
                    >
                      <CatalogAccordion
                        ariaControls="Data Store Accordion"
                        expanded={dataStoreExpanded}
                        onToggle={() => setDataStoreExpanded((prev) => !prev)}
                        title={`${t('data_stores')} (${dataStoresForProcessGroup?.length})`}
                        action={
                          <IconButton
                            size="small"
                            onClick={(e) => e.stopPropagation()}
                            data-testid="add-data-store-button"
                            href={`/data-stores/new${currentParentGroupIdSearchParam()}`}
                          >
                            <Add />
                          </IconButton>
                        }
                      >
                        <Box sx={gridProps}>
                          {dataStoresForProcessGroup?.map(
                            (dataStore: DataStore) => (
                              <DataStoreCard
                                key={dataStore.id}
                                dataStore={dataStore}
                              />
                            ),
                          )}
                        </Box>
                      </CatalogAccordion>
                    </Can>
                  </CardContent>
                </Card>
              )}
            </Stack>
          </Stack>
        </Container>
      )}
    </Box>
  );
}
