import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
// @ts-ignore
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
      <>
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
        <h1>Edit Process Model: {(processModel as any).id}</h1>
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
