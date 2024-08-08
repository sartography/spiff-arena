import React from 'react';
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
} from '@mui/material';
import { AccessTime, PlayArrow } from '@mui/icons-material';
import { useNavigate } from 'react-router';
import DateAndTimeService from '../../services/DateAndTimeService';
import SpiffTooltip from '../../components/SpiffTooltip';
import { ProcessInstance, ProcessInstanceTask } from '../../interfaces';

type TaskTableProps = {
  entries: ProcessInstanceTask[] | ProcessInstance[] | null;
  viewMode?: string;
};

export default function TaskTable({
  entries,
  viewMode = 'table',
}: TaskTableProps) {
  // const [viewMode, setViewMode] = useState<'table' | 'tile'>('table');
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
    const taskUrl = `/tasks/${getProcessInstanceId(entry)}/${entry.task_id}`;
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
    return <span title={fullUsernameString}>{shortUsernameString}</span>;
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

  const renderTable = () => {
    if (!entries) {
      return null;
    }
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
          <TableBody>
            {entries.map((entry) => (
              <TableRow key={entry.id}>
                <TableCell>
                  <Typography variant="body2">
                    {getProcessInstanceId(entry)}
                  </Typography>
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
                    {entry.task_name || entry.task_title}
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
                  >
                    <AccessTime sx={{ fontSize: 'small', mr: 0.5 }} />
                    {DateAndTimeService.convertSecondsToFormattedDateTime(
                      entry.created_at_in_seconds,
                    )}
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
                  >
                    <AccessTime sx={{ fontSize: 'small', mr: 0.5 }} />
                    {DateAndTimeService.convertSecondsToFormattedDateTime(
                      entry.created_at_in_seconds,
                    )}
                  </Typography>
                </TableCell>
                <TableCell>{getWaitingForTableCellComponent(entry)}</TableCell>
                <TableCell>
                  {'task_id' in entry && entry.task_id ? (
                    <SpiffTooltip title="Complete task">
                      <IconButton onClick={() => handleRunTask(entry)}>
                        <PlayArrow />
                      </IconButton>
                    </SpiffTooltip>
                  ) : null}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  const renderTiles = () => {
    if (!entries) {
      return null;
    }
    return (
      <Grid container spacing={2}>
        {entries.map((entry) => (
          <Grid item key={entry.id} xs={12} sm={6} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {entry.process_model_display_name}
                </Typography>
                <Typography variant="body2" paragraph>
                  {entry.task_name || entry.task_title}
                </Typography>
                {getProcessInstanceSummary(entry)}
                <Typography variant="body2" paragraph>
                  Created by: {entry.process_initiator_username}
                </Typography>
                <Typography
                  variant="body2"
                  color="textSecondary"
                  sx={{ display: 'flex', alignItems: 'center' }}
                  paragraph
                >
                  <AccessTime sx={{ fontSize: 'small', mr: 0.5 }} />
                  {DateAndTimeService.convertSecondsToFormattedDateTime(
                    entry.created_at_in_seconds,
                  )}
                </Typography>
                <Typography
                  variant="body2"
                  sx={{ display: 'flex', alignItems: 'center' }}
                >
                  Last milestone: {entry.last_milestone_bpmn_name}
                </Typography>
                <Typography
                  variant="body2"
                  color="textSecondary"
                  sx={{ display: 'flex', alignItems: 'center' }}
                  paragraph
                >
                  Last updated:{' '}
                  {DateAndTimeService.convertSecondsToFormattedDateTime(
                    entry.created_at_in_seconds,
                  )}
                </Typography>
                <Typography variant="body2" paragraph>
                  Waiting for: {getWaitingForTableCellComponent(entry)}
                </Typography>
                <SpiffTooltip title="Complete task">
                  <IconButton onClick={() => handleRunTask(entry)}>
                    <PlayArrow />
                  </IconButton>
                </SpiffTooltip>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    );
  };

  if (entries) {
    return viewMode === 'table' ? renderTable() : renderTiles();
  }
  return null;
}
