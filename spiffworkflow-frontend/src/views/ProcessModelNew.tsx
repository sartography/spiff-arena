import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Box, Typography } from '@mui/material'; // Import MUI components
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import { ProcessModel } from '../interfaces';
import ProcessModelForm from '../components/ProcessModelForm';
import {
  unModifyProcessIdentifierForPathParam,
  setPageTitle,
} from '../helpers';

export default function ProcessModelNew() {
  const { t } = useTranslation();
  const params = useParams();
  const [processModel, setProcessModel] = useState<ProcessModel>({
    id: '',
    display_name: '',
    description: '',
    primary_file_name: '',
    primary_process_id: '',
    files: [],
  });
  setPageTitle([t('add_new_process_model')]);

  return (
    <Box>
      <ProcessBreadcrumb
        hotCrumbs={[
          [t('process_groups'), '/process-groups'],
          {
            entityToExplode: params.process_group_id || '',
            entityType: 'process-group-id',
            linkLastItem: true,
          },
        ]}
      />
      <Typography variant="h1">{t('add_process_model')}</Typography>
      <Box mt={2}>
        <ProcessModelForm
          mode="new"
          processGroupId={unModifyProcessIdentifierForPathParam(
            params.process_group_id || '',
          )}
          processModel={processModel}
          setProcessModel={setProcessModel}
        />
      </Box>
    </Box>
  );
}
