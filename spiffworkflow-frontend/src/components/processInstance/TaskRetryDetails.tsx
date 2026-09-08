import { Alert, Typography } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { BasicTask } from '../../interfaces';
import DateAndTimeService from '../../services/DateAndTimeService';
import FormattedDateTime from '../FormattedDateTime';

type TaskRetryDetailsProps = {
  task: BasicTask;
};

export default function TaskRetryDetails({ task }: TaskRetryDetailsProps) {
  const { t } = useTranslation();
  const retryAt = task.properties_json.internal_data?.spiff__retry_at;
  const retriesAttempted =
    task.properties_json.internal_data?.spiff__retries_attempted;
  const configuredRetries = task.task_definition_properties_json.retries;

  if (
    typeof retriesAttempted === 'undefined' &&
    typeof retryAt === 'undefined'
  ) {
    return null;
  }

  const retryAtInSeconds =
    typeof retryAt === 'undefined' ? null : Number(retryAt);
  const formattedRetryAt =
    retryAtInSeconds === null || Number.isNaN(retryAtInSeconds)
      ? null
      : DateAndTimeService.convertSecondsToFormattedDateTime(retryAtInSeconds);
  const configuredRetriesNumber =
    typeof configuredRetries === 'undefined' ? null : Number(configuredRetries);
  const retriesAttemptedNumber =
    typeof retriesAttempted === 'undefined' ? null : Number(retriesAttempted);
  const normalizedRetriesAttempted =
    retriesAttemptedNumber === null || Number.isNaN(retriesAttemptedNumber)
      ? null
      : Math.max(0, retriesAttemptedNumber);
  const retriesRemaining =
    normalizedRetriesAttempted === null ||
    configuredRetriesNumber === null ||
    Number.isNaN(configuredRetriesNumber)
      ? null
      : Math.max(configuredRetriesNumber - normalizedRetriesAttempted, 0);

  return (
    <Alert severity="info" className="with-tiny-bottom-margin">
      <Typography variant="subtitle2" component="div">
        {t('task_retry_details')}
      </Typography>
      {typeof configuredRetries !== 'undefined' ? (
        <dl>
          <Typography component="dt" variant="subtitle2">
            {t('configured_retries')}:
          </Typography>
          <Typography component="dd" variant="body2">
            {configuredRetries}
          </Typography>
        </dl>
      ) : null}
      <dl>
        <Typography component="dt" variant="subtitle2">
          {t('retries_remaining')}:
        </Typography>
        <Typography component="dd" variant="body2">
          {retriesRemaining ?? 'N/A'}
        </Typography>
      </dl>
      {formattedRetryAt ? (
        <dl>
          <Typography component="dt" variant="subtitle2">
            {t('next_retry_attempt')}:
          </Typography>
          <Typography component="dd" variant="body2">
            <FormattedDateTime seconds={retryAtInSeconds} />
          </Typography>
        </dl>
      ) : null}
    </Alert>
  );
}
