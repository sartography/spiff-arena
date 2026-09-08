import Grid from '@mui/material/Grid';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { BasicTask } from '../../interfaces';

type HistoricalStateBannerProps = {
  taskToTimeTravelTo: BasicTask | null;
  processInstanceShowPageBaseUrl: string;
};

export default function HistoricalStateBanner({
  taskToTimeTravelTo,
  processInstanceShowPageBaseUrl,
}: HistoricalStateBannerProps) {
  const { t } = useTranslation();
  if (!taskToTimeTravelTo) {
    return null;
  }
  const title = `${taskToTimeTravelTo.id}: ${taskToTimeTravelTo.guid}: ${taskToTimeTravelTo.bpmn_identifier}`;
  return (
    <>
      <Grid container spacing={2}>
        <Grid size={{ xs: 12 }}>
          <p>
            {t('viewing_process_instance_at_time_when')}{' '}
            <span title={title}>
              <strong>
                {taskToTimeTravelTo.bpmn_name ||
                  taskToTimeTravelTo.bpmn_identifier}
              </strong>
            </span>{' '}
            {t('was_active')}.{' '}
            <Link
              reloadDocument
              data-testid="process-instance-view-active-task-link"
              to={processInstanceShowPageBaseUrl}
            >
              {t('view_current_process_instance_state')}.
            </Link>
          </p>
        </Grid>
      </Grid>
      <br />
    </>
  );
}
