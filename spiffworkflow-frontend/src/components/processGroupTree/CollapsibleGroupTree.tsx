import { ReactNode, useState } from 'react';
import { Box, Chip, Collapse, Typography, useTheme } from '@mui/material';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import FolderIcon from '@mui/icons-material/Folder';
import { ProcessGroup, ProcessModel } from '../../interfaces';

export interface ModelRowContext {
  depth: number;
  expanded: boolean;
  toggle: () => void;
}

interface CollapsibleGroupTreeProps {
  processGroups: ProcessGroup[];
  renderModelRow: (model: ProcessModel, ctx: ModelRowContext) => ReactNode;
  getGroupInstanceCount?: (groupId: string) => number;
  getModelInstanceCount?: (modelId: string) => number;
  sortProcessModels?: (models: ProcessModel[]) => ProcessModel[];
  showEmptyGroupsAndModels?: boolean;
  defaultExpandedGroupIds?: string[];
  renderGroupMetadata?: (group: ProcessGroup, count: number) => ReactNode;
  emptyText?: string;
}

const INDENT_PER_LEVEL = 2.5;

export default function CollapsibleGroupTree({
  processGroups,
  renderModelRow,
  getGroupInstanceCount,
  getModelInstanceCount,
  sortProcessModels,
  showEmptyGroupsAndModels = true,
  defaultExpandedGroupIds,
  renderGroupMetadata,
  emptyText,
}: CollapsibleGroupTreeProps) {
  const groupRowBackgroundColor =
    useTheme().palette.mode === 'dark'
      ? 'background.light'
      : 'background.mediumlight';
  const [expandedIds, setExpandedIds] = useState<Set<string>>(
    () => new Set(defaultExpandedGroupIds ?? []),
  );

  const toggle = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const renderGroup = (group: ProcessGroup, depth: number): ReactNode => {
    const count = getGroupInstanceCount ? getGroupInstanceCount(group.id) : 0;
    if (!showEmptyGroupsAndModels && getGroupInstanceCount && count === 0) {
      return null;
    }
    const expanded = expandedIds.has(group.id);
    const childGroups = group.process_groups ?? [];
    let childModels = group.process_models ?? [];
    if (sortProcessModels) {
      childModels = sortProcessModels(childModels);
    }
    if (!showEmptyGroupsAndModels && getModelInstanceCount) {
      childModels = childModels.filter((m) => getModelInstanceCount(m.id) > 0);
    }

    return (
      <Box key={group.id} data-testid={`group-tree-node-${group.id}`}>
        <Box
          role="button"
          tabIndex={0}
          aria-expanded={expanded}
          onClick={() => toggle(group.id)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              toggle(group.id);
            }
          }}
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            cursor: 'pointer',
            py: 1,
            pl: depth * INDENT_PER_LEVEL + 1,
            pr: 2,
            borderBottom: '1px solid',
            borderColor: 'borders.primary',
            backgroundColor: groupRowBackgroundColor,
            '&:hover': { backgroundColor: 'action.hover' },
          }}
        >
          {expanded ? (
            <ExpandMoreIcon fontSize="small" />
          ) : (
            <ChevronRightIcon fontSize="small" />
          )}
          <FolderIcon fontSize="small" color="action" />
          <Typography sx={{ fontWeight: 700 }}>{group.display_name}</Typography>
          <Box sx={{ flexGrow: 1 }} />
          {renderGroupMetadata ? (
            renderGroupMetadata(group, count)
          ) : getGroupInstanceCount ? (
            <Chip size="small" label={count} />
          ) : null}
        </Box>
        <Collapse in={expanded} unmountOnExit>
          {childGroups.map((child) => renderGroup(child, depth + 1))}
          {childModels.map((model) =>
            renderModelRow(model, {
              depth: depth + 1,
              expanded: expandedIds.has(model.id),
              toggle: () => toggle(model.id),
            }),
          )}
        </Collapse>
      </Box>
    );
  };

  const rendered = processGroups
    .map((group) => renderGroup(group, 0))
    .filter((node) => node !== null);

  if (rendered.length === 0 && emptyText) {
    return (
      <Typography variant="body1" sx={{ p: 2, color: 'text.secondary' }}>
        {emptyText}
      </Typography>
    );
  }

  return <Box>{rendered}</Box>;
}
