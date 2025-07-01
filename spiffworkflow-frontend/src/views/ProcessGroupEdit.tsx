import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';
// @ts-ignore
import { Box, Typography } from '@mui/material';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import HttpService from '../services/HttpService';
import ProcessGroupForm from '../components/ProcessGroupForm';
import { ProcessGroup } from '../interfaces';
import { setPageTitle } from '../helpers';

export default function ProcessGroupEdit() {
  const params = useParams();
  const [processGroup, setProcessGroup] = useState<ProcessGroup | null>(null);

  useEffect(() => {
    const setProcessGroupsFromResult = (result: any) => {
      setProcessGroup(result);
    };

    HttpService.makeCallToBackend({
      path: `/process-groups/${params.process_group_id}`,
      successCallback: setProcessGroupsFromResult,
    });
  }, [params.process_group_id]);

  const { t } = useTranslation();

  useEffect(() => {
    if (processGroup) {
      setPageTitle([
        t('editing_process_group', { name: processGroup.display_name }),
      ]);
    }
  }, [processGroup, t]);

  if (processGroup) {
    return (
      <>
        <ProcessBreadcrumb
          hotCrumbs={[
            [t('process_groups'), '/process-groups'],
            {
              entityToExplode: processGroup,
              entityType: 'process-group',
              linkLastItem: true,
            },
          ]}
        />
        <Typography variant="h1">
          {t('edit_process_group_with_id', { id: (processGroup as any).id })}
        </Typography>
        <Box mt={2}>
          <ProcessGroupForm
            mode="edit"
            processGroup={processGroup}
            setProcessGroup={setProcessGroup}
          />
        </Box>
      </>
    );
  }
  return null;
}
