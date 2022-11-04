import { useState, useEffect, useContext } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
// @ts-ignore
import { Button, Stack } from '@carbon/react';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import HttpService from '../services/HttpService';
import ButtonWithConfirmation from '../components/ButtonWithConfirmation';
import ErrorContext from '../contexts/ErrorContext';

export default function ProcessModelEdit() {
  const [displayName, setDisplayName] = useState('');
  const params = useParams();
  const navigate = useNavigate();
  const [processModel, setProcessModel] = useState(null);
  const setErrorMessage = (useContext as any)(ErrorContext)[1];

  const processModelPath = `process-models/${params.process_group_id}/${params.process_model_id}`;

  useEffect(() => {
    const processResult = (result: any) => {
      setProcessModel(result);
      setDisplayName(result.display_name);
    };
    HttpService.makeCallToBackend({
      path: `/${processModelPath}`,
      successCallback: processResult,
    });
  }, [processModelPath]);

  const navigateToProcessModel = (_result: any) => {
    navigate(`/admin/${processModelPath}`);
  };

  const navigateToProcessModels = (_result: any) => {
    navigate(`/admin/process-groups/${params.process_group_id}`);
  };

  const updateProcessModel = (event: any) => {
    const processModelToUse = processModel as any;
    event.preventDefault();
    const processModelToPass = Object.assign(processModelToUse, {
      display_name: displayName,
    });
    HttpService.makeCallToBackend({
      path: `/${processModelPath}`,
      successCallback: navigateToProcessModel,
      httpMethod: 'PUT',
      postBody: processModelToPass,
    });
  };

  const deleteProcessModel = () => {
    setErrorMessage(null);
    const processModelToUse = processModel as any;
    const processModelShowPath = `/process-models/${processModelToUse.process_group_id}/${processModelToUse.id}`;
    HttpService.makeCallToBackend({
      path: `${processModelShowPath}`,
      successCallback: navigateToProcessModels,
      httpMethod: 'DELETE',
      failureCallback: setErrorMessage,
    });
  };

  const onDisplayNameChanged = (newDisplayName: any) => {
    setDisplayName(newDisplayName);
  };

  if (processModel) {
    return (
      <>
        <ProcessBreadcrumb processGroupId={(processModel as any).id} />
        <h2>Edit Process Group: {(processModel as any).id}</h2>
        <form onSubmit={updateProcessModel}>
          <label>Display Name:</label>
          <input
            name="display_name"
            type="text"
            value={displayName}
            onChange={(e) => onDisplayNameChanged(e.target.value)}
          />
          <br />
          <br />
          <Stack orientation="horizontal" gap={3}>
            <Button type="submit">Submit</Button>
            <Button variant="secondary" href={`/admin/${processModelPath}`}>
              Cancel
            </Button>
            <ButtonWithConfirmation
              description={`Delete Process Model ${(processModel as any).id}?`}
              onConfirmation={deleteProcessModel}
              buttonLabel="Delete"
            />
          </Stack>
        </form>
      </>
    );
  }
  return null;
}
