import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchEventSource } from '@microsoft/fetch-event-source';
// @ts-ignore
import { Loading, Button } from '@carbon/react';
import { BACKEND_BASE_URL } from '../config';
import { getBasicHeaders } from '../services/HttpService';

// @ts-ignore
import InstructionsForEndUser from './InstructionsForEndUser';
import ProcessBreadcrumb from './ProcessBreadcrumb';
import { ProcessInstance, ProcessInstanceTask } from '../interfaces';
import useAPIError from '../hooks/UseApiError';

type OwnProps = {
  processInstanceId: number;
  modifiedProcessModelIdentifier: string;
  allowRedirect: boolean;
};

export default function ProcessInterstitial({
  processInstanceId,
  modifiedProcessModelIdentifier,
  allowRedirect,
}: OwnProps) {
  const [data, setData] = useState<any[]>([]);
  const [lastTask, setLastTask] = useState<any>(null);
  const [state, setState] = useState<string>('RUNNING');
  const [processInstance, setProcessInstance] =
    useState<ProcessInstance | null>(null);
  const processInstanceShowPageBaseUrl = `/admin/process-instances/for-me/${modifiedProcessModelIdentifier}`;
  const navigate = useNavigate();
  const userTasks = useMemo(() => {
    return ['User Task', 'Manual Task'];
  }, []);
  const { addError } = useAPIError();

  useEffect(() => {
    fetchEventSource(`${BACKEND_BASE_URL}/tasks/${processInstanceId}`, {
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
      onclose() {
        setState('CLOSED');
      },
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // it is critical to only run this once.

  const shouldRedirect = useCallback(
    (myTask: ProcessInstanceTask): boolean => {
      return (
        allowRedirect &&
        !processInstance &&
        myTask &&
        myTask.can_complete &&
        userTasks.includes(myTask.type)
      );
    },
    [userTasks, processInstance]
  );

  useEffect(() => {
    // Added this seperate use effect so that the timer interval will be cleared if
    // we end up redirecting back to the TaskShow page.
    if (shouldRedirect(lastTask)) {
      lastTask.properties.instructionsForEndUser = '';
      const timerId = setInterval(() => {
        navigate(`/tasks/${lastTask.process_instance_id}/${lastTask.id}`);
      }, 2000);
      return () => clearInterval(timerId);
    }
    return undefined;
  }, [lastTask, navigate, userTasks, shouldRedirect]);

  const getStatus = (): string => {
    if (processInstance) {
      return 'LOCKED';
    }
    if (!lastTask.can_complete && userTasks.includes(lastTask.type)) {
      return 'LOCKED';
    }
    if (state === 'CLOSED') {
      return lastTask.state;
    }
    return state;
  };

  const getLoadingIcon = () => {
    if (getStatus() === 'RUNNING') {
      return (
        <Loading
          description="Active loading indicator"
          withOverlay={false}
          style={{ margin: 'auto' }}
        />
      );
    }
    return null;
  };

  const getReturnHomeButton = (index: number) => {
    if (
      index === 0 &&
      !shouldRedirect(lastTask) &&
      ['WAITING', 'ERROR', 'LOCKED', 'COMPLETED', 'READY'].includes(getStatus())
    ) {
      return (
        <div style={{ padding: '10px 0 0 0' }}>
          <Button
            kind="secondary"
            data-qa="return-to-home-button"
            onClick={() => navigate(`/tasks`)}
            style={{ marginBottom: 30 }}
          >
            Return to Home
          </Button>
        </div>
      );
    }
    return '';
  };

  const userMessage = (myTask: ProcessInstanceTask) => {
    if (!processInstance || processInstance.status === 'completed') {
      if (!myTask.can_complete && userTasks.includes(myTask.type)) {
        return (
          <p>
            This next task is assigned to a different person or team. There is
            no action for you to take at this time.
          </p>
        );
      }
      if (shouldRedirect(myTask)) {
        return <div>Redirecting you to the next task now ...</div>;
      }
      if (myTask && myTask.can_complete && userTasks.includes(myTask.type)) {
        return `The task ${myTask.title} is ready for you to complete.`;
      }
      if (myTask.error_message) {
        return <div>{myTask.error_message}</div>;
      }
    }

    let message =
      'There are no additional instructions or information for this task.';
    if (processInstance && processInstance.status !== 'completed') {
      message = `The tasks cannot be completed on this instance because its status is "${processInstance.status}".`;
    }

    return (
      <div>
        <InstructionsForEndUser task={myTask} defaultMessage={message} />
      </div>
    );
  };

  /** In the event there is no task information and the connection closed,
   * redirect to the home page. */
  if (state === 'CLOSED' && lastTask === null) {
    navigate(`/tasks`);
  }

  if (lastTask) {
    return (
      <>
        <ProcessBreadcrumb
          hotCrumbs={[
            ['Process Groups', '/admin'],
            {
              entityToExplode: lastTask.process_model_identifier,
              entityType: 'process-model-id',
              linkLastItem: true,
            },
            [
              `Process Instance: ${processInstanceId}`,
              `${processInstanceShowPageBaseUrl}/${processInstanceId}`,
            ],
          ]}
        />
        {getLoadingIcon()}
        <div style={{ maxWidth: 800, margin: 'auto', padding: 50 }}>
          {data.map((d, index) => (
            <>
              <div
                className={
                  index < 4
                    ? `user_instructions_${index}`
                    : `user_instructions_4`
                }
              >
                {userMessage(d)}
              </div>
              {getReturnHomeButton(index)}
            </>
          ))}
        </div>
      </>
    );
  }
  return null;
}
