import { useState } from 'react';
import { useParams } from 'react-router-dom';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import { ProcessModel } from '../interfaces';
import ProcessModelForm from '../components/ProcessModelForm';
import {
  unModifyProcessIdentifierForPathParam,
  setPageTitle,
} from '../helpers';

export default function ProcessModelNew() {
  const params = useParams();
  const [processModel, setProcessModel] = useState<ProcessModel>({
    id: '',
    display_name: '',
    description: '',
    primary_file_name: '',
    primary_process_id: '',
    files: [],
  });
  setPageTitle(['Add New Process Model']);

  return (
    <>
      <ProcessBreadcrumb
        hotCrumbs={[
          ['Process Groups', '/process-groups'],
          {
            entityToExplode: params.process_group_id || '',
            entityType: 'process-group-id',
            linkLastItem: true,
          },
        ]}
      />
      <h1>Add Process Model</h1>
      <ProcessModelForm
        mode="new"
        processGroupId={unModifyProcessIdentifierForPathParam(
          params.process_group_id || '',
        )}
        processModel={processModel}
        setProcessModel={setProcessModel}
      />
    </>
  );
}
