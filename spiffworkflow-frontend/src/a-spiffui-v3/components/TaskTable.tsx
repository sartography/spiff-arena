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
} from '@mui/material';
import { AccessTime, PlayArrow } from '@mui/icons-material';
import DateAndTimeService from '../../services/DateAndTimeService';
import SpiffTooltip from '../../components/SpiffTooltip';
import { ProcessInstanceTask } from '../../interfaces';

const mainBlue = 'primary.main';

interface TaskTableProps {
  tasks: ProcessInstanceTask[];
  handleRunTask: (task: ProcessInstanceTask) => void;
  getWaitingForTableCellComponent: (task: ProcessInstanceTask) => JSX.Element;
}

const TaskTable: React.FC<TaskTableProps> = ({
  tasks,
  handleRunTask,
  getWaitingForTableCellComponent,
}) => {
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
          {tasks.map((task) => (
            <TableRow key={task.id}>
              <TableCell>
                <Chip
                  label={task.process_model_display_name}
                  size="small"
                  sx={{
                    bgcolor: '#E0E0E0',
                    color: '#616161',
                    mb: 1,
                    fontWeight: 'normal',
                  }}
                />
                <Typography variant="body2" paragraph>
                  {task.task_name || task.task_title}
                </Typography>
                <Typography variant="body2" color={mainBlue}>
                  {task.process_instance_summary}
                </Typography>
              </TableCell>
              <TableCell>
                <Typography variant="body2" paragraph>
                  {task.process_initiator_username}
                </Typography>
                <Typography
                  variant="body2"
                  color="textSecondary"
                  sx={{ display: 'flex', alignItems: 'center' }}
                >
                  <AccessTime sx={{ fontSize: 'small', mr: 0.5 }} />
                  {DateAndTimeService.convertSecondsToFormattedDateTime(
                    task.created_at_in_seconds,
                  )}
                </Typography>
              </TableCell>
              <TableCell>
                <Typography
                  variant="body2"
                  sx={{ display: 'flex', alignItems: 'center' }}
                >
                  {'● '}
                  {task.last_milestone_bpmn_name}
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
                    task.created_at_in_seconds,
                  )}
                </Typography>
              </TableCell>
              <TableCell>{getWaitingForTableCellComponent(task)}</TableCell>
              <TableCell>
                <SpiffTooltip title="Complete task">
                  <IconButton onClick={() => handleRunTask(task)}>
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
};

export default TaskTable;
