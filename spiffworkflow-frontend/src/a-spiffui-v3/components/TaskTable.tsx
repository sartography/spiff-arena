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
} from '@mui/material';
import { AccessTime, PlayArrow } from '@mui/icons-material';
import DateAndTimeService from '../../services/DateAndTimeService';
import SpiffTooltip from '../../components/SpiffTooltip';
import { ProcessInstance, ProcessInstanceTask } from '../../interfaces';

const mainBlue = 'primary.main';

type TaskTableProps = {
  entries: ProcessInstanceTask[] | ProcessInstance[] | null;
  handleRunTask: (item: ProcessInstanceTask | ProcessInstance) => void;
  getWaitingForTableCellComponent: (
    entry: ProcessInstanceTask | ProcessInstance,
  ) => ReactElement;
};

export default function TaskTable({
  entries,
  handleRunTask,
  getWaitingForTableCellComponent,
}: TaskTableProps) {
  if (entries) {
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
                  <Typography variant="body2" color={mainBlue}>
                    {entry.process_instance_summary}
                  </Typography>
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
                  <SpiffTooltip title="Complete task">
                    <IconButton onClick={() => handleRunTask(entry)}>
                      <PlayArrow />
                    </IconButton>
                  </SpiffTooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  }
  return null;
}
