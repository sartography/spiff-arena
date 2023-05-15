import React from 'react';
import { useParams } from 'react-router-dom';
// @ts-ignore
import ProcessInterstitial from '../components/ProcessInterstitial';

export default function ProcessInterstitialPage() {
  const params = useParams();
  // @ts-ignore
  return (
    <ProcessInterstitial
      processInstanceId={Number(params.process_instance_id)}
      modifiedProcessModelIdentifier={String(
        params.modified_process_model_identifier
      )}
      allowRedirect
    />
  );
}
