import React from 'react';
import { useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
// @ts-ignore
import { Box } from '@mui/material';
import ProcessInterstitial from '../../components/ProcessInterstitial';
import ProcessBreadcrumb from '../../components/ProcessBreadcrumb';
import useProcessInstanceShowPageUrl from '../../hooks/useProcessInstanceShowPageUrl';

type OwnProps = {
  variant: string;
};

export default function ProcessInterstitialPage({ variant }: OwnProps) {
  const { t } = useTranslation();
  const params = useParams();

  const { processInstanceShowPageUrl, permissionsLoaded } =
    useProcessInstanceShowPageUrl(variant);

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
          [t('process_groups'), '/process-groups'],
          {
            entityToExplode: String(params.process_model_id),
            entityType: 'process-model-id',
            linkLastItem: true,
          },
          [
            t('process_with_id', { id: params.process_instance_id }),
            processInstanceShowPageUrl ?? undefined,
          ],
        ]}
      />
      {permissionsLoaded ? (
        <ProcessInterstitial
          processInstanceId={Number(params.process_instance_id)}
          processInstanceShowPageUrl={processInstanceShowPageUrl ?? '/'}
          allowRedirect
        />
      ) : null}
    </Box>
  );
}
