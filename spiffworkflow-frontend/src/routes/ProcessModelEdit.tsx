import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
// @ts-ignore
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import HttpService from '../services/HttpService';
import ProcessModelForm from '../components/ProcessModelForm';
import { ProcessModel } from '../interfaces';

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
    return (
      <>
        <ProcessBreadcrumb
          hotCrumbs={[
            ['Process Groups', '/admin'],
            [
              `Process Model: ${processModel.id}`,
              `process_model:${processModel.id}:link`,
            ],
          ]}
        />
        <h2>Edit Process Model: {(processModel as any).id}</h2>
        <ProcessModelForm
          mode="edit"
          processGroupId={params.process_group_id}
          processModel={processModel}
          setProcessModel={setProcessModel}
        />
      </>
    );
  }
  return null;
}
