import React, { useEffect, useState } from 'react';
import { InlineNotification } from '@carbon/react';

import InstructionsForEndUser from './InstructionsForEndUser';
import { ProcessInstance, ProcessInstanceTask } from '../interfaces';
import { HUMAN_TASK_TYPES } from '../helpers';
import HttpService from '../services/HttpService';

type OwnProps = {
  processInstance: ProcessInstance;
};

export default function ProcessInstanceCurrentTaskInfo({
  processInstance,
}: OwnProps) {
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
    kind: string = 'info',
  ) => {
    return (
      <div>
        <InlineNotification
          kind={kind}
          subtitle={subtitle}
          title={title}
          lowContrast
        />
      </div>
    );
  };

  const taskUserMessage = () => {
    if (!task) {
      return null;
    }

    if (!task.can_complete && HUMAN_TASK_TYPES.includes(task.type)) {
      let message = 'This next task is assigned to a different person or team.';
      if (task.assigned_user_group_identifier) {
        message = `This next task is assigned to group: ${task.assigned_user_group_identifier}.`;
      } else if (task.potential_owner_usernames) {
        let potentialOwnerArray = task.potential_owner_usernames.split(',');
        if (potentialOwnerArray.length > 2) {
          potentialOwnerArray = potentialOwnerArray.slice(0, 2).concat(['...']);
        }
        message = `This next task is assigned to user(s): ${potentialOwnerArray.join(
          ', ',
        )}.`;
      }

      return inlineMessage(
        '',
        `${message} There is no action for you to take at this time.`,
      );
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
        `Process ${processInstance.status}`,
        `This process instance was ${processInstance.status} by an administrator. Please get in touch with them for more information.`,
        'warning',
      );
    }
    if (processInstance.status === 'error') {
      let errMessage = `This process instance experienced an unexpected error and cannot continue. Please get in touch with an administrator for more information and next steps.`;
      if (task && task.error_message) {
        errMessage = ` ${errMessage.concat(task.error_message)}`;
      }
      return inlineMessage(`Process Error`, errMessage, 'error');
    }

    if (task) {
      return taskUserMessage();
    }
    const defaultMsg =
      'There are no additional instructions or information for this process.';
    return inlineMessage(`Process Error`, defaultMsg, 'info');
  };

  if (processInstance && taskResult) {
    return <div className="user_instructions">{userMessage()}</div>;
  }

  return null;
}
