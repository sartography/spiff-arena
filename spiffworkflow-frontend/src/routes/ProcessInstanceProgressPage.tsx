import React from 'react';
import { useParams } from 'react-router-dom';
import ProcessInstanceProgress from '../components/ProcessInstanceProgress';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';

type OwnProps = {
  variant: string;
};

export default function ProcessInstanceProgressPage({ variant }: OwnProps) {
  const params = useParams();
  let processInstanceShowPageUrl = `/process-instances/for-me/${params.process_model_id}/${params.process_instance_id}`;
  if (variant === 'all') {
    processInstanceShowPageUrl = `/process-instances/${params.process_model_id}/${params.process_instance_id}`;
  }

  return (
    <>
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
      <ProcessInstanceProgress
        processInstanceId={Number(params.process_instance_id)}
        processInstanceShowPageUrl={processInstanceShowPageUrl}
      />
    </>
  );
}
