import { ReactNode, useState } from 'react';
import { Box, Chip, Collapse, Typography } from '@mui/material';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { ProcessGroup, ProcessModel } from '../../interfaces';

export interface ModelRowContext {
  depth: number;
  expanded: boolean;
  toggle: () => void;
}

interface CollapsibleGroupTreeProps {
  groups: ProcessGroup[];
  /** Renders the row for a single process model (leaf). */
  renderModelRow: (model: ProcessModel, ctx: ModelRowContext) => ReactNode;
  /** Aggregate instance count for a group; also drives hide-empty. */
  groupInstanceCount?: (groupId: string) => number;
  /** Per-model instance count; used to hide empty models when showEmpty=false. */
  modelInstanceCount?: (modelId: string) => number;
  /** Sort/filter the models within a single group before rendering. */
  sortModels?: (models: ProcessModel[]) => ProcessModel[];
  /** When false, groups/models with a zero instance count are hidden. */
  showEmpty?: boolean;
  /** Group ids expanded on first render. */
  defaultExpandedIds?: string[];
  /** Optional custom right-aligned meta for a group header. */
  renderGroupMeta?: (group: ProcessGroup, count: number) => ReactNode;
  emptyText?: string;
}

const INDENT_PER_LEVEL = 2.5;

export default function CollapsibleGroupTree({
  groups,
  renderModelRow,
  groupInstanceCount,
  modelInstanceCount,
  sortModels,
  showEmpty = true,
  defaultExpandedIds,
  renderGroupMeta,
  emptyText,
}: CollapsibleGroupTreeProps) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(
    () => new Set(defaultExpandedIds ?? []),
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
    const count = groupInstanceCount ? groupInstanceCount(group.id) : 0;
    if (!showEmpty && groupInstanceCount && count === 0) {
      return null;
    }
    const expanded = expandedIds.has(group.id);
    const childGroups = group.process_groups ?? [];
    let childModels = group.process_models ?? [];
    if (sortModels) {
      childModels = sortModels(childModels);
    }
    if (!showEmpty && modelInstanceCount) {
      childModels = childModels.filter((m) => modelInstanceCount(m.id) > 0);
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
            backgroundColor: 'background.bluegreymedium',
            '&:hover': { backgroundColor: 'background.bluegreylight' },
          }}
        >
          {expanded ? (
            <ExpandMoreIcon fontSize="small" />
          ) : (
            <ChevronRightIcon fontSize="small" />
          )}
          <Typography sx={{ fontWeight: 700 }}>{group.display_name}</Typography>
          <Box sx={{ flexGrow: 1 }} />
          {renderGroupMeta ? (
            renderGroupMeta(group, count)
          ) : groupInstanceCount ? (
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

  const rendered = groups
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
