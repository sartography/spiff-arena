import { Chip, Stack, Typography, useTheme } from '@mui/material';
import { useEffect } from 'react';

/**
 * Appears when we need to display process instances in a responsive view.
 * Was quickly made for demo.
 * TODO: Talk to designer about this.
 */
export default function ProcessInstanceCard({
  pi,
}: {
  pi: Record<string, any>;
}) {
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

  useEffect(() => {
    console.log(pi);
  }, []);
  return (
    <Stack
      gap={1}
      sx={{
        width: '100%',
        padding: 1,
        alignContent: 'center',
      }}
    >
      {/* We may or may not want to keep this info in the card
      <Stack direction="row" spacing={2} sx={{ color: 'text.secondary' }}>
        <Typography variant="caption">{`ID: ${pi.row.id}`}</Typography>
        <Typography variant="caption">
          {`Initiator: ${pi.row.process_initiator_username}`}
        </Typography>
      </Stack>
      <Stack direction="row" spacing={2} sx={{ color: 'text.secondary' }}>
        <Typography variant="caption">{`Start: ${formatSecondsForDisplay(
          pi.row.start_in_seconds
        )}`}</Typography>
        <Typography variant="caption">
          {`End: ${formatSecondsForDisplay(pi.row.end_in_seconds) || '...'}`}
        </Typography>
      </Stack> */}

      <Typography variant="button" sx={{ fontWeight: 600 }}>
        ({pi.row.tasks.length}) {pi.row.process_model_display_name}
      </Typography>

      <Stack direction="row" gap={2}>
        <Chip
          label={pi.row.status || '...no info...'}
          variant="filled"
          size="small"
          sx={{
            backgroundColor: chipBackground(pi.row.status),
            borderRadius: 1,
          }}
        />
        <Chip
          label={pi.row.last_milestone_bpmn_name || '...no info...'}
          variant="filled"
          size="small"
          sx={{
            borderRadius: 1,
            backgroundColor: chipBackground(pi.row.last_milestone_bpmn_name),
          }}
        />
      </Stack>
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
