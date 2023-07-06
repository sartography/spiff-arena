import React from 'react';
import { useParams } from 'react-router-dom';
// @ts-ignore
import ProcessInterstitial from '../components/ProcessInterstitial';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';

type OwnProps = {
  variant: string;
};

export default function ProcessInterstitialPage({ variant }: OwnProps) {
  const params = useParams();
  let processInstanceShowPageUrl = `/admin/process-instances/for-me/${params.process_model_id}/${params.process_instance_id}`;
  if (variant === 'all') {
    processInstanceShowPageUrl = `/admin/process-instances/${params.process_model_id}/${params.process_instance_id}`;
  }

  return (
    <>
      <ProcessBreadcrumb
        hotCrumbs={[
          ['Process Groups', '/admin'],
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
    </>
  );
}
