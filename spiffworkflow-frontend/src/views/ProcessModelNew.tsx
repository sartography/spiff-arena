import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Box, Typography, Stack } from '@mui/material';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import { ProcessModel } from '../interfaces';
import ProcessModelForm from '../components/ProcessModelForm';
import { ProcessModelImportButton } from '../components/ProcessModelImportButton';
import { ProcessModelImportDialog } from '../components/ProcessModelImportDialog';
import {
  unModifyProcessIdentifierForPathParam,
  modifyProcessIdentifierForPathParam,
  setPageTitle,
} from '../helpers';

export default function ProcessModelNew() {
  const { t } = useTranslation();
  const params = useParams();
  const navigate = useNavigate();
  const [importDialogOpen, setImportDialogOpen] = useState(false);
  const [processModel, setProcessModel] = useState<ProcessModel>({
    id: '',
    display_name: '',
    description: '',
    primary_file_name: '',
    primary_process_id: '',
    files: [],
  });

  useEffect(() => {
    setPageTitle([t('add_new_process_model')]);
  }, [t]);

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
      <Stack
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        mb={2}
      >
        <Typography variant="h1">{t('add_process_model')}</Typography>
        <ProcessModelImportButton onClick={() => setImportDialogOpen(true)} />
      </Stack>
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
      {params.process_group_id && (
        <ProcessModelImportDialog
          open={importDialogOpen}
          onClose={() => setImportDialogOpen(false)}
          processGroupId={params.process_group_id}
          onImportSuccess={(processModelId) => {
            // Navigate to the imported process model using React Router
            navigate(
              `/process-models/${modifyProcessIdentifierForPathParam(processModelId)}`,
            );
          }}
        />
      )}
    </Box>
  );
}
