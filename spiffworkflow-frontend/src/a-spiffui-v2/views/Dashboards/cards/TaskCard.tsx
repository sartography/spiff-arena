import { Box, Chip, Stack, Typography, useTheme } from '@mui/material';
import { useEffect } from 'react';
import { formatSecondsForDisplay } from '../../../utils/Utils';

/**
 * Appears when we need to display process instances in a responsive view.
 * Was quickly made for demo. Don't put a lot of effort into this.
 */
export default function TaskCard({ task }: { task: Record<string, any> }) {
  const { mode } = useTheme().palette;
  /** These values map to theme tokens, which enable the light/dark modes etc. */
  const chipBackground = (status: string) => {
    switch (status) {
      case 'Completed':
      case 'complete':
        return `info.${mode}`;
      case 'Started':
        return `success.${mode}`;
      case 'error':
        return `error.${mode}`;
      case 'Wait a second':
      case 'user_input_required':
        return `warning.${mode}`;
      default:
        return 'default';
    }
  };

  useEffect(() => {}, [task]);
  return (
    <Stack
      sx={{
        width: '100%',
        padding: 2,
        alignContent: 'center',
      }}
    >
      <Stack direction="row" spacing={2} sx={{ color: 'text.secondary' }}>
        <Typography variant="caption">{`ID: ${task.row.id}`}</Typography>
        <Typography variant="caption">
          {`Initiator: ${task.row.process_initiator_username}`}
        </Typography>
      </Stack>
      <Stack direction="row" spacing={2} sx={{ color: 'text.secondary' }}>
        <Typography variant="caption">{`Start: ${formatSecondsForDisplay(
          task.row.start_in_seconds,
        )}`}</Typography>
        <Typography variant="caption">
          {`End: ${formatSecondsForDisplay(task.row.end_in_seconds) || '...'}`}
        </Typography>
      </Stack>
      <Typography variant="button" sx={{ fontWeight: 600 }}>
        {task.row.task_name}
      </Typography>
      <Box sx={{ paddingTop: 0.5 }}>
        <Chip
          label={task.row.task_status || '...no info...'}
          variant="filled"
          size="small"
          sx={{
            backgroundColor: chipBackground(task.row.task_status),
            borderRadius: 1,
          }}
        />
      </Box>
    </Stack>
  );
}

// "row": {
//       "id": 3,
//       "actions": null,
//       "bpmn_version_control_identifier": "557595e9",
//       "bpmn_version_control_type": "git",
//       "bpmn_xml_file_contents_retrieval_error": null,
//       "bpmn_xml_file_contents": null,
//       "created_at_in_seconds": 1714613156,
//       "end_in_seconds": null,
//       "last_milestone_bpmn_name": null,
//       "process_initiator_id": 1,
//       "process_initiator_username": "admin@spiffworkflow.org",
//       "process_model_display_name": "Call Activity",
//       "process_model_identifier": "misc/category_number_one/call-activity",
//       "start_in_seconds": 1714613156,
//       "status": "error",
//       "task_updated_at_in_seconds": null,
//       "updated_at_in_seconds": 1714613157
//   },
