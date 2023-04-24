import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { fetchEventSource } from '@microsoft/fetch-event-source';
// @ts-ignore
import { Loading, Grid, Column } from '@carbon/react';
import { BACKEND_BASE_URL } from '../config';
import { getBasicHeaders } from '../services/HttpService';

// @ts-ignore
import InstructionsForEndUser from '../components/InstructionsForEndUser';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import { ProcessInstanceTask } from '../interfaces';
import useAPIError from '../hooks/UseApiError';

export default function ProcessInterstitial() {
  const [data, setData] = useState<any[]>([]);
  const [lastTask, setLastTask] = useState<any>(null);
  const [state, setState] = useState<string>('RUNNING');
  const params = useParams();
  const navigate = useNavigate();
  const userTasks = useMemo(() => {
    return ['User Task', 'Manual Task'];
  }, []);
  const { addError } = useAPIError();

  const processInstanceShowPageBaseUrl = `/admin/process-instances/for-me/${params.modified_process_model_identifier}`;

  useEffect(() => {
    fetchEventSource(
      `${BACKEND_BASE_URL}/tasks/${params.process_instance_id}`,
      {
        headers: getBasicHeaders(),
        onmessage(ev) {
          const retValue = JSON.parse(ev.data);
          if ('error_code' in retValue) {
            addError(retValue);
          } else {
            setData((prevData) => [...prevData, retValue]);
            setLastTask(retValue);
          }
        },
        onclose() {
          setState('CLOSED');
        },
      }
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // it is critical to only run this once.

  const shouldRedirect = useCallback(
    (myTask: ProcessInstanceTask): boolean => {
      return myTask && myTask.can_complete && userTasks.includes(myTask.type);
    },
    [userTasks]
  );

  useEffect(() => {
    // Added this seperate use effect so that the timer interval will be cleared if
    // we end up redirecting back to the TaskShow page.
    if (shouldRedirect(lastTask)) {
      setState('REDIRECTING');
      lastTask.properties.instructionsForEndUser = '';
      const timerId = setInterval(() => {
        navigate(`/tasks/${lastTask.process_instance_id}/${lastTask.id}`);
      }, 2000);
      return () => clearInterval(timerId);
    }
    return undefined;
  }, [lastTask, navigate, userTasks, shouldRedirect]);

  const getStatus = (): string => {
    if (!lastTask.can_complete && userTasks.includes(lastTask.type)) {
      return 'LOCKED';
    }
    if (state === 'CLOSED') {
      return lastTask.state;
    }
    return state;
  };

  const getStatusImage = () => {
    switch (getStatus()) {
      case 'RUNNING':
        return (
          <Loading description="Active loading indicator" withOverlay={false} />
        );
      case 'LOCKED':
        return <img src="/interstitial/locked.png" alt="Locked" />;
      case 'READY':
      case 'REDIRECTING':
        return <img src="/interstitial/redirect.png" alt="Redirecting ...." />;
      case 'WAITING':
        return <img src="/interstitial/waiting.png" alt="Waiting ...." />;
      case 'COMPLETED':
        return <img src="/interstitial/completed.png" alt="Completed" />;
      case 'ERROR':
        return <img src="/interstitial/errored.png" alt="Errored" />;
      default:
        return getStatus();
    }
  };

  function capitalize(str: string): string {
    if (str && str.length > 0) {
      return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
    }
    return '';
  }

  const userMessage = (myTask: ProcessInstanceTask) => {
    if (!myTask.can_complete && userTasks.includes(myTask.type)) {
      return <div>This next task must be completed by a different person.</div>;
    }
    if (shouldRedirect(myTask)) {
      return <div>Redirecting you to the next task now ...</div>;
    }
    if (myTask.error_message) {
      return <div>{myTask.error_message}</div>;
    }

    return (
      <div>
        <InstructionsForEndUser task={myTask} />
      </div>
    );
  };

  /** In the event there is no task information and the connection closed,
   * redirect to the home page. */
  if (state === 'closed' && lastTask === null) {
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
              `Process Instance: ${params.process_instance_id}`,
              `${processInstanceShowPageBaseUrl}/${params.process_instance_id}`,
            ],
          ]}
        />
        <div style={{ display: 'flex', alignItems: 'center' }}>
          {getStatusImage()}
          <div>
            <h1 style={{ marginBottom: '0em' }}>
              {lastTask.process_model_display_name}:{' '}
              {lastTask.process_instance_id}
            </h1>
            <div>Status: {capitalize(getStatus())}</div>
          </div>
        </div>
        <br />
        <br />
        {data.map((d) => (
          <Grid fullWidth style={{ marginBottom: '1em' }}>
            <Column md={2} lg={4} sm={2}>
              Task: <em>{d.title}</em>
            </Column>
            <Column md={6} lg={6} sm={4}>
              {userMessage(d)}
            </Column>
          </Grid>
        ))}
      </>
    );
  }
  return null;
}
