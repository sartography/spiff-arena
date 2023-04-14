import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { BACKEND_BASE_URL } from '../config';
import { getBasicHeaders } from '../services/HttpService';

export default function ProcessInterstitial() {
  const [data, setData] = useState<any[]>([]);
  const params = useParams();

  useEffect(() => {
    fetchEventSource(
      `${BACKEND_BASE_URL}/tasks/${params.process_instance_id}`,
      {
        headers: getBasicHeaders(),
        onmessage(ev) {
          console.log(data, ev.data);
          const parsedData = JSON.parse(ev.data);
          setData((data) => [...data, parsedData]);
        },
      }
    );
  }, []);

  return <div className="App">The last streamed item was: {data}</div>;
}
