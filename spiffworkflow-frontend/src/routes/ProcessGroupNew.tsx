import { useState } from 'react';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import ProcessGroupForm from '../components/ProcessGroupForm';
import { ProcessGroup } from '../interfaces';

export default function ProcessGroupNew() {
  const [processGroup, setProcessGroup] = useState<ProcessGroup>({
    id: '',
    display_name: '',
    description: '',
  });

  return (
    <>
      <ProcessBreadcrumb />
      <h2>Add Process Group</h2>
      <ProcessGroupForm
        mode="new"
        processGroup={processGroup}
        setProcessGroup={setProcessGroup}
      />
    </>
  );
}
