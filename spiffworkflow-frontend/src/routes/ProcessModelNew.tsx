import { useState } from 'react';
import { useParams } from 'react-router-dom';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import { ProcessModel } from '../interfaces';
import ProcessModelForm from '../components/ProcessModelForm';

export default function ProcessModelNew() {
  const params = useParams();

  const [processModel, setProcessModel] = useState<ProcessModel>({
    id: '',
    display_name: '',
    description: '',
    process_group_id: params.process_group_id || '',
    primary_file_name: '',
    files: [],
  });

  return (
    <>
      <ProcessBreadcrumb />
      <h2>Add Process Model</h2>
      <ProcessModelForm
        mode="new"
        processModel={processModel}
        setProcessModel={setProcessModel}
      />
    </>
  );
}
