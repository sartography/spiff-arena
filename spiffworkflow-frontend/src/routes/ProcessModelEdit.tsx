import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Box, Typography } from '@mui/material';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import HttpService from '../services/HttpService';
import ProcessModelForm from '../components/ProcessModelForm';
import { ProcessModel } from '../interfaces';
import { setPageTitle } from '../helpers';

export default function ProcessModelEdit() {
  const params = useParams();
  const [processModel, setProcessModel] = useState<ProcessModel | null>(null);
  const processModelPath = `process-models/${params.process_model_id}`;

  useEffect(() => {
    HttpService.makeCallToBackend({
      path: `/${processModelPath}`,
      successCallback: setProcessModel,
    });
  }, [processModelPath]);

  if (processModel) {
    setPageTitle([`Editing ${processModel.display_name}`]);
    return (
      <Box>
        <ProcessBreadcrumb
          hotCrumbs={[
            ['Process Groups', '/process-groups'],
            {
              entityToExplode: processModel,
              entityType: 'process-model',
              linkLastItem: true,
            },
          ]}
        />
        <Typography variant="h1">
          Edit Process Model: {(processModel as any).id}
        </Typography>
        <Box mt={2}>
          <ProcessModelForm
            mode="edit"
            processGroupId={params.process_group_id}
            processModel={processModel}
            setProcessModel={setProcessModel}
          />
        </Box>
      </Box>
    );
  }
  return null;
}
