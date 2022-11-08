import { useState } from 'react';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import { ProcessModel } from '../interfaces';
import ProcessModelForm from '../components/ProcessModelForm';

export default function ProcessModelNew() {
  const [processModel, setProcessModel] = useState<ProcessModel>({
    id: '',
    display_name: '',
    description: '',
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
