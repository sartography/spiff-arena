import React, { useEffect, useState } from 'react';
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

export default function ProcessInterstitial() {
  const [data, setData] = useState<any[]>([]);
  const [lastTask, setLastTask] = useState<any>(null);
  const [status, setStatus] = useState<string>('running');
  const params = useParams();
  const navigate = useNavigate();
  const userTasks = ['User Task', 'Manual Task'];

  useEffect(() => {
    fetchEventSource(
      `${BACKEND_BASE_URL}/tasks/${params.process_instance_id}`,
      {
        headers: getBasicHeaders(),
        onmessage(ev) {
          console.log(data, ev.data);
          const task = JSON.parse(ev.data);
          setData((prevData) => [...prevData, task]);
          setLastTask(task);
        },
        onclose() {
          setStatus('closed');
          console.log('Connection Closed by the Server');
        },
      }
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // it is critical to only run this once.

  useEffect(() => {
    // Added this seperate use effect so that the timer interval will be cleared if
    // we end up redirecting back to the TaskShow page.
    if (
      lastTask &&
      lastTask.can_complete &&
      userTasks.includes(lastTask.type)
    ) {
      const timerId = setInterval(() => {
        navigate(`/tasks/${lastTask.process_instance_id}/${lastTask.id}`);
      }, 1000);
      return () => clearInterval(timerId);
    }
    return undefined;
  }, [lastTask]);

  const processStatusImage = () => {
    if (status !== 'running') {
      setStatus(lastTask.state);
    }
    if (!lastTask.can_complete && userTasks.includes(lastTask.type)) {
      setStatus('LOCKED');
    }
    switch (status) {
      case 'running':
        return (
          <Loading description="Active loading indicator" withOverlay={false} />
        );
      case 'WAITING':
        return <img src="/interstitial/clock.png" alt="Waiting ...." />;
      case 'COMPLETED':
        return <img src="/interstitial/checkmark.png" alt="Completed" />;
      case 'LOCKED':
        return (
          <img
            src="/interstitial/lock.png"
            alt="Locked, Waiting on someone else."
          />
        );
      default:
        return null;
    }
  };

  const userMessage = (myTask: ProcessInstanceTask) => {
    if (!myTask.can_complete && userTasks.includes(myTask.type)) {
      return <div>This next task must be completed by a different person.</div>;
    }
    return (
      <div>
        <InstructionsForEndUser task={myTask} />
      </div>
    );
  };

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
            [`Process Instance Id: ${lastTask.process_instance_id}`],
          ]}
        />
        <h1 style={{ display: 'inline-flex', alignItems: 'center' }}>
          {processStatusImage()}
          {lastTask.process_model_display_name}: {lastTask.process_instance_id}
        </h1>

        <Grid condensed fullWidth>
          <Column md={6} lg={8} sm={4}>
            {data &&
              data.map((d) => (
                <div
                  style={{ display: 'flex', alignItems: 'center', gap: '2em' }}
                >
                  <div>
                    Task: <em>{d.title}</em>
                  </div>
                  <div>{userMessage(d)}</div>
                </div>
              ))}
          </Column>
        </Grid>
      </>
    );
  }
  return null;
}
