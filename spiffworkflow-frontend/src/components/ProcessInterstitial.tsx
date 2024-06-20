import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchEventSource } from '@microsoft/fetch-event-source';
// @ts-ignore
import { Loading, InlineNotification } from '@carbon/react';
import { BACKEND_BASE_URL } from '../config';
import { getBasicHeaders } from '../services/HttpService';

// @ts-ignore
import InstructionsForEndUser from './InstructionsForEndUser';
import { ProcessInstance, ProcessInstanceTask } from '../interfaces';
import useAPIError from '../hooks/UseApiError';
import { HUMAN_TASK_TYPES } from '../helpers';

type OwnProps = {
  processInstanceId: number;
  processInstanceShowPageUrl: string;
  allowRedirect: boolean;
  smallSpinner?: boolean;
  collapsableInstructions?: boolean;
  executeTasks?: boolean;
};

export default function ProcessInterstitial({
  processInstanceId,
  allowRedirect,
  processInstanceShowPageUrl,
  smallSpinner = false,
  collapsableInstructions = false,
  executeTasks = true,
}: OwnProps) {
  const [data, setData] = useState<any[]>([]);
  const [lastTask, setLastTask] = useState<any>(null);
  const [state, setState] = useState<string>('RUNNING');
  const [processInstance, setProcessInstance] =
    useState<ProcessInstance | null>(null);

  const navigate = useNavigate();
  const { addError } = useAPIError();

  useEffect(() => {
    fetchEventSource(
      `${BACKEND_BASE_URL}/tasks/${processInstanceId}?execute_tasks=${executeTasks}`,
      {
        headers: getBasicHeaders(),
        onmessage(ev) {
          const retValue = JSON.parse(ev.data);
          if (retValue.type === 'error') {
            addError(retValue.error);
          } else if (retValue.type === 'task') {
            setData((prevData) => [retValue.task, ...prevData]);
            setLastTask(retValue.task);
          } else if (retValue.type === 'unrunnable_instance') {
            setProcessInstance(retValue.unrunnable_instance);
          }
        },
        onerror(error: any) {
          // if backend returns a 500 then stop attempting to load the task
          setState('CLOSED');
          // we know that this server sent events lib gets these sorts of errors when you are on another tab or window while it is working.
          // it's fine
          const wasAbortedError = /\baborted\b/.test(error.message);
          if (!wasAbortedError) {
            addError(error);
            throw error;
          }
        },
        onclose() {
          setState('CLOSED');
        },
      },
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // it is critical to only run this once.

  const shouldRedirectToTask = useCallback(
    (myTask: ProcessInstanceTask): boolean => {
      return (
        allowRedirect &&
        !processInstance &&
        myTask &&
        myTask.can_complete &&
        HUMAN_TASK_TYPES.includes(myTask.type)
      );
    },
    [allowRedirect, processInstance],
  );

  const shouldRedirectToProcessInstance = useCallback((): boolean => {
    return allowRedirect && state === 'CLOSED';
  }, [allowRedirect, state]);

  useEffect(() => {
    // Added this separate use effect so that the timer interval will be cleared if
    // we end up redirecting back to the TaskShow page.
    if (shouldRedirectToTask(lastTask)) {
      lastTask.properties.instructionsForEndUser = '';
      const timerId = setInterval(() => {
        navigate(`/tasks/${lastTask.process_instance_id}/${lastTask.id}`);
      }, 500);
      return () => clearInterval(timerId);
    }
    if (shouldRedirectToProcessInstance()) {
      // Navigate without pause as we will be showing the same information.
      navigate(processInstanceShowPageUrl);
    }
    return undefined;
  }, [
    lastTask,
    navigate,
    shouldRedirectToTask,
    processInstanceId,
    processInstanceShowPageUrl,
    state,
    shouldRedirectToProcessInstance,
  ]);

  const getLoadingIcon = () => {
    if (state === 'RUNNING') {
      let style = { margin: '50px 0 50px 50px' };
      if (smallSpinner) {
        style = { margin: '2x 5px 2px 2px' };
      }
      return (
        <Loading
          description="Active loading indicator"
          withOverlay={false}
          small={smallSpinner}
          style={style}
        />
      );
    }
    return null;
  };

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

  const userMessageForProcessInstance = (
    pi: ProcessInstance,
    myTask: ProcessInstanceTask | null = null,
  ) => {
    if (['terminated', 'suspended'].includes(pi.status)) {
      return inlineMessage(
        `Process ${pi.status}`,
        `This process instance was ${pi.status} by an administrator. Please get in touch with them for more information.`,
        'warning',
      );
    }
    if (pi.status === 'error') {
      let errMessage = `This process instance experienced an unexpected error and can not continue. Please get in touch with an administrator for more information and next steps. `;
      if (myTask && myTask.error_message) {
        errMessage = errMessage.concat(myTask.error_message);
      }
      return inlineMessage(`Process Error`, errMessage, 'error');
    }
    // Otherwise we are not started, waiting, complete, or user_input_required
    const defaultMsg =
      'There are no additional instructions or information for this process.';
    if (myTask) {
      return (
        <InstructionsForEndUser
          task={myTask}
          defaultMessage={defaultMsg}
          allowCollapse={collapsableInstructions}
        />
      );
    }
    return inlineMessage(`Process Error`, defaultMsg, 'info');
  };

  const userMessage = (myTask: ProcessInstanceTask) => {
    if (processInstance) {
      return userMessageForProcessInstance(processInstance, myTask);
    }

    if (!myTask.can_complete && HUMAN_TASK_TYPES.includes(myTask.type)) {
      let message = 'This next task is assigned to a different person or team.';
      if (myTask.assigned_user_group_identifier) {
        message = `This next task is assigned to group: ${myTask.assigned_user_group_identifier}.`;
      } else if (myTask.potential_owner_usernames) {
        let potentialOwnerArray = myTask.potential_owner_usernames.split(',');
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
    if (shouldRedirectToTask(myTask)) {
      return inlineMessage('', `Redirecting ...`);
    }
    if (
      myTask &&
      myTask.can_complete &&
      HUMAN_TASK_TYPES.includes(myTask.type)
    ) {
      return inlineMessage(
        '',
        `The task "${myTask.title}" is ready for you to complete.`,
      );
    }
    if (myTask.error_message) {
      return inlineMessage('Error', myTask.error_message, 'error');
    }
    return (
      <div>
        <InstructionsForEndUser
          task={myTask}
          defaultMessage="There are no additional instructions or information for this task."
          allowCollapse={collapsableInstructions}
        />
      </div>
    );
  };

  /** In the event there is no task information and the connection closed,
   * redirect to the home page. */
  if (state === 'CLOSED' && lastTask === null && allowRedirect) {
    // Favor redirecting to the process instance show page
    if (processInstance) {
      navigate(processInstanceShowPageUrl);
    } else {
      navigate(`/tasks`);
    }
  }

  let displayableData = data;
  if (state === 'CLOSED') {
    displayableData = [data[0]];
  }

  const className = (index: number) => {
    if (displayableData.length === 1) {
      return 'user_instructions';
    }
    return index < 4 ? `user_instructions_${index}` : `user_instructions_4`;
  };

  if (lastTask) {
    return (
      <div>
        {getLoadingIcon()}
        {displayableData.map((d, index) => (
          <div className={className(index)}>{userMessage(d)}</div>
        ))}
      </div>
    );
  }
  if (processInstance) {
    return (
      <div>
        {getLoadingIcon()}
        {userMessageForProcessInstance(processInstance)}
      </div>
    );
  }
  return <div>{getLoadingIcon()}</div>;
}
