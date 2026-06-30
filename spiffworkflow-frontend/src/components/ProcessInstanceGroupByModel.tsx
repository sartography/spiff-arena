import { useTranslation } from 'react-i18next';
import {
  Box,
  Chip,
  CircularProgress,
  Collapse,
  Typography,
} from '@mui/material';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import {
  ProcessGroup,
  ProcessModel,
  ReportFilter,
  ReportMetadata,
} from '../interfaces';
import { modifyProcessIdentifierForPathParam } from '../helpers';
import CollapsibleGroupTree, {
  ModelRowContext,
} from './processGroupTree/CollapsibleGroupTree';
import useProcessGroupTree from './processGroupTree/useProcessGroupTree';
import ProcessInstanceListTable from './ProcessInstanceListTable';

interface ProcessInstanceGroupByModelProps {
  /** The base report metadata (columns + user's active filters) to compose with. */
  reportMetadata: ReportMetadata;
  variant?: string;
}

/**
 * Odoo-style "group by process group" view of process instances. Renders the
 * nested process-group hierarchy with exact instance counts (derived from
 * /process-models/stats, no backend group-by). Expanding a model leaf lazily
 * loads that model's instances by composing the base filters with an exact
 * process_model_identifier filter. Groups with zero instances are hidden.
 */
export default function ProcessInstanceGroupByModel({
  reportMetadata,
  variant = 'for-me',
}: ProcessInstanceGroupByModelProps) {
  const { t } = useTranslation();
  const { processGroups, loading, groupInstanceCount, modelInstanceCount } =
    useProcessGroupTree();

  const renderModelRow = (model: ProcessModel, ctx: ModelRowContext) => {
    const count = modelInstanceCount(model.id);
    const mergedReportMetadata: ReportMetadata = {
      ...reportMetadata,
      filter_by: [
        ...reportMetadata.filter_by.filter(
          (f) => f.field_name !== 'process_model_identifier',
        ),
        {
          field_name: 'process_model_identifier',
          field_value: model.id,
          operator: 'equals',
        } as ReportFilter,
      ],
    };
    const paginationPrefix = `pg_${modifyProcessIdentifierForPathParam(model.id)}`;
    return (
      <Box
        key={model.id}
        data-testid={`group-tree-instances-model-${modifyProcessIdentifierForPathParam(
          model.id,
        )}`}
      >
        <Box
          role="button"
          tabIndex={0}
          aria-expanded={ctx.expanded}
          onClick={ctx.toggle}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              ctx.toggle();
            }
          }}
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            cursor: 'pointer',
            py: 0.75,
            pl: ctx.depth * 2.5 + 2.5,
            pr: 2,
            borderBottom: '1px solid',
            borderColor: 'borders.primary',
            backgroundColor: 'background.paper',
            '&:hover': { backgroundColor: 'action.hover' },
          }}
        >
          {ctx.expanded ? (
            <ExpandMoreIcon fontSize="small" />
          ) : (
            <ChevronRightIcon fontSize="small" />
          )}
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            {model.display_name}
          </Typography>
          <Box sx={{ flexGrow: 1 }} />
          <Chip size="small" label={count} />
        </Box>
        <Collapse in={ctx.expanded} unmountOnExit>
          <Box sx={{ pl: ctx.depth * 2.5 + 4, pr: 1, py: 1 }}>
            <ProcessInstanceListTable
              variant={variant}
              reportMetadata={mergedReportMetadata}
              paginationQueryParamPrefix={paginationPrefix}
              perPageOptions={[5, 10, 25]}
              textToShowIfEmpty={t('no_results')}
            />
          </Box>
        </Collapse>
      </Box>
    );
  };

  if (loading || !processGroups) {
    return (
      <Box sx={{ p: 2, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <CollapsibleGroupTree
      processGroups={processGroups as ProcessGroup[]}
      renderModelRow={renderModelRow}
      getGroupInstanceCount={groupInstanceCount}
      getModelInstanceCount={modelInstanceCount}
      showEmptyGroupsAndModels={false}
      emptyText={t('no_results')}
      renderGroupMetadata={(_group, count) => (
        <Chip size="small" label={t('n_runs', { count })} />
      )}
    />
  );
}
