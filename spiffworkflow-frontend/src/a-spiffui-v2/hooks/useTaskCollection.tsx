import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import HttpService from '../../services/HttpService';

/**
 * Grab tasks using HttpService from the Spiff API.
 * TODO: We'll need to allow appending the path to hit different endpoints.
 * Right now we're just grabbing for-me
 */
export default function useTaskCollection({
  processInfo,
}: {
  processInfo: Record<string, any>;
}) {
  const [taskCollection, setTaskCollection] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(false);

  /**
   * Query function to get tasks from the backend
   * @returns Query functions must return a value, even if it's just true
   */
  const processResult = (result: any[]) => {
    setTaskCollection(result);
    setLoading(false);
  };

  const path = '/tasks';
  const getTaskCollection = async () => {
    setLoading(true);
    // TODO: Currently, the API endpoint for this is an SSE endpoint, so we can't use the HttpService.
    // We'll need to refactor this to use the SSE service, or change the API to return a RESTful response.
    // const path = processInfo?.id ? `/tasks/${processInfo.id}` : '/tasks';
    HttpService.makeCallToBackend({
      path,
      httpMethod: 'GET',
      successCallback: processResult,
    });

    return true;
  };

  /** TanStack (React Query) trigger to do it's SWR state/cache thing */
  useQuery({
    queryKey: [path, processInfo],
    queryFn: () => getTaskCollection(),
  });

  return {
    taskCollection,
    loading,
  };
}

// Example taskCollection object:
//   "id": "f3e909d4-451f-4374-a285-a0f3a4689d62",
//   "form_file_name": "form3.json",
//   "task_type": "UserTask",
//   "ui_form_file_name": "form3_ui.json",
//   "task_status": "READY",
//   "updated_at_in_seconds": 1715349007,
//   "process_model_display_name": "Process Model With Form",
//   "process_instance_id": 17,
//   "created_at_in_seconds": 1715183498,
//   "bpmn_process_identifier": "test_form",
//   "lane_assignment_id": null,
//   "task_guid": "f3e909d4-451f-4374-a285-a0f3a4689d62",
//   "completed": false,
//   "task_id": "f3e909d4-451f-4374-a285-a0f3a4689d62",
//   "completed_by_user_id": null,
//   "task_name": "form3",
//   "actual_owner_id": null,
//   "task_title": "get_form_num_three",
//   "process_model_identifier": "misc/category_number_one/process-model-with-form",
//   "process_instance_status": "user_input_required",
//   "process_initiator_username": "admin@spiffworkflow.org",
//   "assigned_user_group_identifier": null,
//   "potential_owner_usernames": "admin@spiffworkflow.org"
// }
