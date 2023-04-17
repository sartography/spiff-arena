import { useEffect, useState } from 'react';
import {useNavigate, useParams} from 'react-router-dom';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { BACKEND_BASE_URL } from '../config';
import { getBasicHeaders } from '../services/HttpService';
import {Task} from '../interfaces';
import InstructionsForEndUser from '../components/InstructionsForEndUser';

export default function ProcessInterstitial() {
  const [data, setData] = useState<any[]>([]);
  const [lastTask, setLastTask] = useState<any>(null);
  const params = useParams();
  const navigate = useNavigate();

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
          console.log("Connection Closed by the Server");
        },
      }
    );
  }, []);

  useEffect(() => {
    // Added this seperate use effect so that the timer interval will be cleared if
    // we end up redirecting back to the TaskShow page.
    if (lastTask && ['User Task', 'Manual Task'].includes(lastTask.type)) {
      const timerId = setInterval(() => {
        navigate(`/tasks/${lastTask.process_instance_id}/${lastTask.id}`);
      }, 1000);
      return () => clearInterval(timerId);
    }
    return undefined;
  }, [lastTask]);


  return (
    <div className="container">
      <h3 className="p-3 text-center">React - Display a list of items</h3>
      <table className="table table-striped table-bordered">
        <thead>
          <tr>
            <th>Task Title</th>
          </tr>
        </thead>
        <tbody>
          {data &&
            data.map((d) => (
              <tr key={d.id}>
                <td>{d.title}</td>
                <td>{d.state}</td>
                <td>{d.type}</td>
                <td>
                  <InstructionsForEndUser task={d} />
                </td>
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  );
}
