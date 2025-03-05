import React from 'react';
import { useParams } from 'react-router-dom';
// @ts-ignore
import { Box } from '@mui/material';
import ProcessInterstitial from '../../components/ProcessInterstitial';
import ProcessBreadcrumb from '../../components/ProcessBreadcrumb';

type OwnProps = {
  variant: string;
};

export default function ProcessInterstitialPage({ variant }: OwnProps) {
  const params = useParams();

  // TODO: the next version we should support the pi show page in the new ui
  // let processInstanceShowPageUrl = `/process-instances/for-me/${params.process_model_id}/${params.process_instance_id}`;
  let processInstanceShowPageUrl = '/';
  if (variant === 'all') {
    processInstanceShowPageUrl = `/process-instances/${params.process_model_id}/${params.process_instance_id}`;
  }

  return (
    <Box
      component="main"
      sx={{
        flexGrow: 1,
        p: 3,
        overflow: 'hidden',
        height: '100vh',
      }}
    >
      <ProcessBreadcrumb
        hotCrumbs={[
          ['Process Groups', '/process-groups'],
          {
            entityToExplode: String(params.process_model_id),
            entityType: 'process-model-id',
            linkLastItem: true,
          },
          [
            `Process Instance: ${params.process_instance_id}`,
            `${processInstanceShowPageUrl}`,
          ],
        ]}
      />
      <ProcessInterstitial
        processInstanceId={Number(params.process_instance_id)}
        processInstanceShowPageUrl={processInstanceShowPageUrl}
        allowRedirect
      />
    </Box>
  );
}
