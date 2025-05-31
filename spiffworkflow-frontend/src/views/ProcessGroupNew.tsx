import { useState } from 'react';
import { useTranslation } from 'react-i18next';
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
  const { t } = useTranslation();

  setPageTitle([t('new_process_group')]);

  const hotCrumbs: HotCrumbItem[] = [[t('process_groups'), '/process-groups']];
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
        {t('add_process_group')}
      </Typography>
      <ProcessGroupForm
        mode="new"
        processGroup={processGroup}
        setProcessGroup={setProcessGroup}
      />
    </>
  );
}
