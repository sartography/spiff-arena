import { useState } from 'react';
import { Typography } from '@mui/material';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import ProcessGroupForm from '../components/ProcessGroupForm';
import { ProcessGroup, HotCrumbItem } from '../interfaces';
import { setPageTitle } from '../helpers';

export default function ProcessGroupNew() {
  const searchParams = new URLSearchParams(document.location.search);
  const parentGroupId = searchParams.get('parentGroupId');
  const [processGroup, setProcessGroup] = useState<ProcessGroup>({
    id: '',
    display_name: '',
    description: '',
  });
  setPageTitle(['New Process Group']);

  const hotCrumbs: HotCrumbItem[] = [['Process Groups', '/process-groups']];
  if (parentGroupId) {
    hotCrumbs.push({
      entityToExplode: parentGroupId,
      entityType: 'process-group-id',
      linkLastItem: true,
    });
  }

  return (
    <>
      <ProcessBreadcrumb hotCrumbs={hotCrumbs} />
      <Typography variant="h1" gutterBottom>
        Add Process Group
      </Typography>
      <ProcessGroupForm
        mode="new"
        processGroup={processGroup}
        setProcessGroup={setProcessGroup}
      />
    </>
  );
}
