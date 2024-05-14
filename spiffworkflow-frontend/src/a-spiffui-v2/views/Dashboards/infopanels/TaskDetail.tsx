import { ReactNode } from 'react';

const path = `/task-data/modified_process_model_identifier/process_instance_id/task_guid`;

export default function TaskDetail({
  task,
  icon,
  styleOverride,
}: {
  task: Record<string, any>;
  icon: ReactNode;
  styleOverride?: Record<string, any>;
}) {}
