import { useEffect } from 'react';
import useProcessModels from '../../hooks/useProcessModels';
import useProcessGroups from '../../hooks/useProcessGroups';

export default function StartProcess() {
  const { processGroups } = useProcessGroups({ processInfo: {} });

  useEffect(() => {
    if (processGroups?.results?.length) {
      console.log(processGroups);
    }
  }, [processGroups]);

  return (
    <div>
      <h1>StartProcess</h1>
    </div>
  );
}
