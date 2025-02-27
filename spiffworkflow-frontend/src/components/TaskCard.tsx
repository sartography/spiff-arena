import React, { ReactElement } from 'react';
import {
  Card,
  CardContent,
  Typography,
  IconButton,
  Chip,
  Grid,
  Container,
} from '@mui/material';
import { PlayArrow } from '@mui/icons-material';
import { ProcessInstance, ProcessInstanceTask } from '../interfaces';

type TaskCardProps = {
  entry: ProcessInstanceTask | ProcessInstance;
  waitingFor: ReactElement | null;
  hasAccessToCompleteTask: boolean;
};

export default function TaskCard({
  entry,
  waitingFor,
  hasAccessToCompleteTask,
}: TaskCardProps) {
  return (
    <Grid item key={entry.id} xs={12} sm={6} md={4}>
      <Card
        onClick={() => hasAccessToCompleteTask && handleRunTask(entry)}
        sx={{
          display: 'flex',
          flexDirection: 'column',
          height: '100%',
          position: 'relative',
        }}
      >
        <CardContent sx={{ flex: '1 0 auto' }}>
          {hasAccessToCompleteTask ? (
            <IconButton sx={{ position: 'absolute', top: 8, right: 8 }}>
              <PlayArrow />
            </IconButton>
          ) : null}
          <Typography variant="h6" gutterBottom>
            <Chip
              label={entry.process_model_display_name}
              size="small"
              sx={{
                bgcolor: '#E0E0E0',
                color: '#616161',
                mb: 1,
                fontWeight: 'normal',
              }}
            />
          </Typography>
          <Typography variant="body2" paragraph>
            {entry.task_title || entry.task_name}
          </Typography>
          {getProcessInstanceSummary(entry)}
          <br />
        </CardContent>
        <Container
          id="workflow-details"
          sx={{
            mb: 2,
            px: {
              xs: '16px',
              sm: '16px',
              md: '16px',
            },
          }}
        >
          <Typography variant="body2">
            <strong>Created by</strong>: {entry.process_initiator_username}
          </Typography>
          <Typography
            variant="body2"
            sx={{ display: 'flex', alignItems: 'center' }}
          >
            <strong>Last milestone</strong>:{' '}
            {entry.last_milestone_bpmn_name}
          </Typography>
          {waitingFor ? (
            <Typography variant="body2">
              <strong>Waiting for</strong>: {waitingFor}
            </Typography>
          ) : null}
        </Container>
      </Card>
    </Grid>
  );

  function getProcessInstanceSummary(
    entry: ProcessInstanceTask | ProcessInstance
  ) {
    let summary = null;
    if ('summary' in entry) {
      summary = entry.summary;
    }
    if ('process_instance_summary' in entry) {
      summary = entry.process_instance_summary;
    }
    if (!summary) {
      return null;
    }
    return (
      <Typography variant="body2" color="primary.main">
        {summary}
      </Typography>
    );
  }

  function handleRunTask(entry: ProcessInstanceTask | ProcessInstance) {
    const taskUrl = `/tasks/${getProcessInstanceId(entry)}/${entry.task_id}`;
    navigate(taskUrl);
  };

  function getProcessInstanceId(
    entry: ProcessInstanceTask | ProcessInstance,
  ) {
    if ('process_instance_id' in entry) {
      return entry.process_instance_id;
    }
    if ('id' in entry) {
      return entry.id;
    }
    return null;
  };
}
