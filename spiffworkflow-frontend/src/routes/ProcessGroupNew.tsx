import { useState } from 'react';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import ProcessGroupForm from '../components/ProcessGroupForm';
import { ProcessGroup, HotCrumbItem } from '../interfaces';

export default function ProcessGroupNew() {
  const searchParams = new URLSearchParams(document.location.search);
  const parentGroupId = searchParams.get('parentGroupId');
  const [processGroup, setProcessGroup] = useState<ProcessGroup>({
    id: '',
    display_name: '',
    description: '',
  });

  const hotCrumbs: HotCrumbItem[] = [['Process Groups', '/admin']];
  if (parentGroupId) {
    hotCrumbs.push(['', `process_group:${parentGroupId}:link`]);
  }

  return (
    <>
      <ProcessBreadcrumb hotCrumbs={hotCrumbs} />
      <h1>Add Process Group</h1>
      <ProcessGroupForm
        mode="new"
        processGroup={processGroup}
        setProcessGroup={setProcessGroup}
      />
    </>
  );
}
