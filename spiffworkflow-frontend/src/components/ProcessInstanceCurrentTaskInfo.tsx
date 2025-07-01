import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
// Import Alert from MUI
import Alert from '@mui/material/Alert';

import InstructionsForEndUser from './InstructionsForEndUser';
import { ProcessInstance, ProcessInstanceTask } from '../interfaces';
import { getProcessStatus, HUMAN_TASK_TYPES } from '../helpers';
import HttpService from '../services/HttpService';

type OwnProps = {
  processInstance: ProcessInstance;
};

export default function ProcessInstanceCurrentTaskInfo({
  processInstance,
}: OwnProps) {
  const { t } = useTranslation();
  const [taskResult, setTaskResult] = useState<any>(null);
  const [task, setTask] = useState<ProcessInstanceTask | null>(null);

  useEffect(() => {
    const processTaskResult = (result: any) => {
      setTaskResult(result);
      setTask(result.task);
    };
    HttpService.makeCallToBackend({
      path: `/tasks/${processInstance.id}/instruction`,
      successCallback: processTaskResult,
      failureCallback: (error: any) => console.error(error.message),
    });
  }, [processInstance]);

  const inlineMessage = (
    title: string,
    subtitle: string,
    severity: 'info' | 'warning' | 'error' = 'info',
  ) => {
    return (
      <div>
        {/* Use MUI Alert component */}
        <Alert severity={severity}>
          <strong>{title}</strong> {subtitle}
        </Alert>
      </div>
    );
  };

  const taskUserMessage = () => {
    if (!task) {
      return null;
    }

    if (!task.can_complete && HUMAN_TASK_TYPES.includes(task.type)) {
      let message = t('task_assigned_different_person');
      if (task.assigned_user_group_identifier) {
        message = t('task_assigned_group', {
          group: task.assigned_user_group_identifier,
        });
      } else if (task.potential_owner_usernames) {
        let potentialOwnerArray = task.potential_owner_usernames.split(',');
        if (potentialOwnerArray.length > 2) {
          potentialOwnerArray = potentialOwnerArray.slice(0, 2).concat(['...']);
        }
        message = t('task_assigned_users', {
          users: potentialOwnerArray.join(', '),
        });
      }

      return inlineMessage('', `${message} ${t('no_action_required')}`);
    }
    if (task && task.can_complete && HUMAN_TASK_TYPES.includes(task.type)) {
      return null;
    }
    return (
      <div>
        <InstructionsForEndUser task={task} allowCollapse />
      </div>
    );
  };

  const userMessage = () => {
    if (!processInstance) {
      return null;
    }
    if (['terminated', 'suspended'].includes(processInstance.status)) {
      return inlineMessage(
        t('process_status', { status: getProcessStatus(processInstance) }),
        t('process_status_by_admin', {
          status: getProcessStatus(processInstance),
        }),
        'warning',
      );
    }
    if (processInstance.status === 'error') {
      let errMessage = t('process_error_msg');
      if (task && task.error_message) {
        errMessage = `${errMessage} ${task.error_message}`;
      }
      return inlineMessage(t('process_error'), errMessage, 'error');
    }

    if (task) {
      return taskUserMessage();
    }
    const defaultMsg = t('no_additional_instructions');
    return inlineMessage(t('process_error'), defaultMsg, 'info');
  };

  if (processInstance && taskResult) {
    return <div className="user_instructions">{userMessage()}</div>;
  }

  return null;
}
