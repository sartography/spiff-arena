import {
  Check as Checkmark,
  Autorenew as InProgress,
  PauseCircleOutline as PauseOutline,
  StopCircleOutlined,
  WarningAmber as Warning,
} from '@mui/icons-material';
import { Chip, Link as MuiLink, Typography } from '@mui/material';
import Grid from '@mui/material/Grid';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import {
  getLastMilestoneFromProcessInstance,
  getProcessStatus,
  isURL,
  modifyProcessIdentifierForPathParam,
  truncateString,
} from '../../helpers';
import { ProcessInstance } from '../../interfaces';
import FormattedDateTime from '../FormattedDateTime';

type ProcessInstanceSummaryProps = {
  processInstance: ProcessInstance;
};

function formatMetadataValue(key: string, value: string) {
  if (isURL(value)) {
    return (
      <MuiLink href={value} target="_blank" rel="noopener noreferrer">
        {key} link
      </MuiLink>
    );
  }
  return value;
}

export default function ProcessInstanceSummary({
  processInstance,
}: ProcessInstanceSummaryProps) {
  const { t } = useTranslation();
  let lastUpdatedTimeLabel = t('process_updated');
  let lastUpdatedTime = processInstance.task_updated_at_in_seconds;
  if (processInstance.end_in_seconds) {
    lastUpdatedTimeLabel = t('process_completed');
    lastUpdatedTime = processInstance.end_in_seconds;
  }

  let statusIcon = <InProgress />;
  if (processInstance.status === 'suspended') {
    statusIcon = <PauseOutline />;
  } else if (processInstance.status === 'complete') {
    statusIcon = <Checkmark />;
  } else if (processInstance.status === 'terminated') {
    statusIcon = <StopCircleOutlined />;
  } else if (processInstance.status === 'error') {
    statusIcon = <Warning />;
  }

  const [lastMilestoneFullValue, lastMilestoneTruncatedValue] =
    getLastMilestoneFromProcessInstance(processInstance);

  return (
    <Grid container spacing={2}>
      <Grid size={{ xs: 12, sm: 6 }}>
        <dl>
          <Typography component="dt" variant="subtitle2">
            {t('status')}:
          </Typography>
          <Typography component="dd" variant="body2">
            <Chip
              label={getProcessStatus(processInstance)}
              icon={statusIcon}
              data-testid="process-instance-status-chip"
              size="small"
            />
          </Typography>
        </dl>
        <dl>
          <Typography component="dt" variant="subtitle2">
            {t('started_by')}:
          </Typography>
          <Typography component="dd" variant="body2">
            {' '}
            {processInstance.process_initiator_username}
          </Typography>
        </dl>
        {processInstance.process_model_with_diagram_identifier ? (
          <dl>
            <Typography component="dt" variant="subtitle2">
              {t('current_diagram')}:{' '}
            </Typography>
            <Typography component="dd" variant="body2">
              <Link
                data-testid="go-to-current-diagram-process-model"
                to={`/process-models/${modifyProcessIdentifierForPathParam(
                  processInstance.process_model_with_diagram_identifier,
                )}`}
              >
                {processInstance.process_model_with_diagram_identifier}
              </Link>
            </Typography>
          </dl>
        ) : null}
        <dl>
          <Typography component="dt" variant="subtitle2">
            {t('started')}:
          </Typography>
          <Typography component="dd" variant="body2">
            <FormattedDateTime
              seconds={processInstance.start_in_seconds || 0}
            />
          </Typography>
        </dl>
        <dl>
          <Typography component="dt" variant="subtitle2">
            {lastUpdatedTimeLabel}:
          </Typography>
          <Typography component="dd" variant="body2">
            <FormattedDateTime
              seconds={lastUpdatedTime || 0}
              placeholder="N/A"
            />
          </Typography>
        </dl>
        <dl>
          <Typography component="dt" variant="subtitle2">
            {t('last_milestone')}:
          </Typography>
          <Typography
            component="dd"
            variant="body2"
            title={lastMilestoneFullValue}
          >
            {lastMilestoneTruncatedValue}
          </Typography>
        </dl>
        <dl>
          <Typography component="dt" variant="subtitle2">
            {t('revision')}:
          </Typography>
          <Typography component="dd" variant="body2">
            {processInstance.bpmn_version_control_identifier} (
            {processInstance.bpmn_version_control_type})
          </Typography>
        </dl>
      </Grid>
      <Grid size={{ xs: 12, sm: 6 }}>
        {(processInstance.process_metadata || []).map(
          (processInstanceMetadata) => (
            <dl className="metadata-display" key={processInstanceMetadata.key}>
              <Typography
                component="dt"
                variant="subtitle2"
                title={processInstanceMetadata.key}
              >
                {truncateString(processInstanceMetadata.key, 50)}:
              </Typography>
              <Typography
                component="dd"
                variant="body2"
                data-testid={`metadata-value-${processInstanceMetadata.key}`}
              >
                {formatMetadataValue(
                  processInstanceMetadata.key,
                  processInstanceMetadata.value,
                )}
              </Typography>
            </dl>
          ),
        )}
      </Grid>
    </Grid>
  );
}
