import React, { ReactElement } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  IconButton,
  Chip,
  Grid,
  Card,
  CardContent,
  Container,
} from '@mui/material';
import { AccessTime, PlayArrow } from '@mui/icons-material';
import { useNavigate } from 'react-router';
import SpiffTooltip from '../../components/SpiffTooltip';
import { ProcessInstance, ProcessInstanceTask } from '../../interfaces';
import UserService from '../../services/UserService';
import { TimeAgo } from '../../helpers/timeago';
import DateAndTimeService from '../../services/DateAndTimeService';

type TaskTableProps = {
  entries: ProcessInstanceTask[] | ProcessInstance[] | null;
  viewMode?: string;
  showNonActive?: boolean;
};

export default function TaskTable({
  entries,
  viewMode = 'table',
  showNonActive = false,
}: TaskTableProps) {
  const navigate = useNavigate();

  const getProcessInstanceId = (
    entry: ProcessInstanceTask | ProcessInstance,
  ) => {
    if ('process_instance_id' in entry) {
      return entry.process_instance_id;
    }
    if ('id' in entry) {
      return entry.id;
    }
    return null;
  };

  const handleRunTask = (entry: ProcessInstanceTask | ProcessInstance) => {
    const taskUrl = `/newui/tasks/${getProcessInstanceId(entry)}/${entry.task_id}`;
    navigate(taskUrl);
  };

  const getWaitingForTableCellComponent = (
    entry: ProcessInstanceTask | ProcessInstance,
  ) => {
    let fullUsernameString = '';
    let shortUsernameString = '';
    if (entry.potential_owner_usernames) {
      fullUsernameString = entry.potential_owner_usernames;
      const usernames = entry.potential_owner_usernames.split(',');
      const firstTwoUsernames = usernames.slice(0, 2);
      if (usernames.length > 2) {
        firstTwoUsernames.push('...');
      }
      shortUsernameString = firstTwoUsernames.join(',');
    }
    if (entry.assigned_user_group_identifier) {
      fullUsernameString = entry.assigned_user_group_identifier;
      shortUsernameString = entry.assigned_user_group_identifier;
    }
    if (shortUsernameString) {
      return <span title={fullUsernameString}>{shortUsernameString}</span>;
    }
    return null;
  };

  const getProcessInstanceSummary = (
    entry: ProcessInstanceTask | ProcessInstance,
  ) => {
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
  };

  const tableRow = (
    entry: ProcessInstance | ProcessInstanceTask,
    waitingFor: ReactElement | null,
    hasAccessToCompleteTask: boolean,
  ) => {
    return (
      <TableRow key={entry.id}>
        <TableCell>
          <Typography variant="body2">{getProcessInstanceId(entry)}</Typography>
        </TableCell>
        <TableCell>
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
          <Typography variant="body2" paragraph>
            {entry.task_title || entry.task_name}
          </Typography>
          {getProcessInstanceSummary(entry)}
        </TableCell>
        <TableCell>
          <Typography variant="body2" paragraph>
            {entry.process_initiator_username}
          </Typography>
          <Typography
            variant="body2"
            color="textSecondary"
            sx={{ display: 'flex', alignItems: 'center' }}
            title={
              DateAndTimeService.convertSecondsToFormattedDateTime(
                entry.created_at_in_seconds,
              ) || '-'
            }
          >
            <AccessTime sx={{ fontSize: 'small', mr: 0.5 }} />
            {TimeAgo.inWords(entry.created_at_in_seconds)}
          </Typography>
        </TableCell>
        <TableCell>
          <Typography
            variant="body2"
            sx={{ display: 'flex', alignItems: 'center' }}
          >
            {'● '}
            {entry.last_milestone_bpmn_name}
          </Typography>
        </TableCell>
        <TableCell>
          <Typography
            variant="body2"
            color="textSecondary"
            sx={{ display: 'flex', alignItems: 'center' }}
            title={
              DateAndTimeService.convertSecondsToFormattedDateTime(
                entry.updated_at_in_seconds,
              ) || '-'
            }
          >
            <AccessTime sx={{ fontSize: 'small', mr: 0.5 }} />
            {TimeAgo.inWords(entry.updated_at_in_seconds)}
          </Typography>
        </TableCell>
        <TableCell>{waitingFor}</TableCell>
        <TableCell>
          {hasAccessToCompleteTask ? (
            <SpiffTooltip title="Complete task">
              <IconButton onClick={() => handleRunTask(entry)}>
                <PlayArrow />
              </IconButton>
            </SpiffTooltip>
          ) : null}
        </TableCell>
      </TableRow>
    );
  };

  const renderTable = (records: any) => {
    return (
      <TableContainer
        component={Paper}
        sx={{
          bgcolor: 'background.paper',
          boxShadow: 'none',
          borderWidth: '1px',
          borderStyle: 'solid',
          borderColor: 'borders.table',
        }}
      >
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Id</TableCell>
              <TableCell>Task details</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Last milestone</TableCell>
              <TableCell>Last updated</TableCell>
              <TableCell>Waiting for</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>{records}</TableBody>{' '}
        </Table>
      </TableContainer>
    );
  };

  const tileEntry = (
    entry: ProcessInstance | ProcessInstanceTask,
    waitingFor: ReactElement | null,
    hasAccessToCompleteTask: boolean,
  ) => {
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
              <strong>Last milestone</strong>: {entry.last_milestone_bpmn_name}
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
  };

  const renderTiles = (records: any) => {
    return (
      <Grid container spacing={2}>
        {records}
      </Grid>
    );
  };

  if (!entries) {
    return null;
  }

  const regex = new RegExp(
    `\\b(${UserService.getPreferredUsername()}|${UserService.getUserEmail()})\\b`,
  );

  const records = entries.map((entry) => {
    if (
      !showNonActive &&
      'status' in entry &&
      ['complete', 'error'].includes(entry.status)
    ) {
      return null;
    }
    let hasAccessToCompleteTask = false;
    if (
      (entry.potential_owner_usernames || '').match(regex) &&
      'task_id' in entry &&
      entry.task_id
    ) {
      hasAccessToCompleteTask = true;
    }
    const waitingFor = getWaitingForTableCellComponent(entry);
    if (viewMode === 'table') {
      return tableRow(entry, waitingFor, hasAccessToCompleteTask);
    }
    return tileEntry(entry, waitingFor, hasAccessToCompleteTask);
  });

  return viewMode === 'table' ? renderTable(records) : renderTiles(records);
}
