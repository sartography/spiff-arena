import { useState, useEffect, useContext } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
// @ts-ignore
import { Button, Stack } from '@carbon/react';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import HttpService from '../services/HttpService';
import ButtonWithConfirmation from '../components/ButtonWithConfirmation';
import ErrorContext from '../contexts/ErrorContext';
import {
  getGroupFromModifiedModelId,
  modifyProcessModelPath,
} from '../helpers';

export default function ProcessModelEdit() {
  const [displayName, setDisplayName] = useState('');
  const params = useParams();
  const navigate = useNavigate();
  const [processModel, setProcessModel] = useState(null);
  const setErrorMessage = (useContext as any)(ErrorContext)[1];

  const processModelPath = `process-models/${params.process_model_id}`;

  useEffect(() => {
    const processResult = (result: any) => {
      setProcessModel(result);
      setDisplayName(result.display_name);
    };
    console.log(`processModelPath: ${processModelPath}`);
    HttpService.makeCallToBackend({
      path: `/${processModelPath}`,
      successCallback: processResult,
    });
  }, [processModelPath]);

  const navigateToProcessModel = (_result: any) => {
    console.log(`processModelPath: ${processModelPath}`);
    navigate(`/admin/${processModelPath}`);
  };

  const navigateToProcessModels = (_result: any) => {
    const processGroupId = getGroupFromModifiedModelId(
      (params as any).process_model_id
    );
    const modifiedProcessGroupId = modifyProcessModelPath(processGroupId);
    navigate(`/admin/process-groups/${modifiedProcessGroupId}`);
  };

  const updateProcessModel = (event: any) => {
    const processModelToUse = processModel as any;
    event.preventDefault();
    const processModelToPass = Object.assign(processModelToUse, {
      display_name: displayName,
    });
    console.log(`processModelPath: ${processModelPath}`);
    HttpService.makeCallToBackend({
      path: `/${processModelPath}`,
      successCallback: navigateToProcessModel,
      httpMethod: 'PUT',
      postBody: processModelToPass,
    });
  };

  // share with or delete from ProcessModelEditDiagram
  const deleteProcessModel = () => {
    setErrorMessage(null);
    const processModelToUse = processModel as any;
    const modifiedProcessModelId: String = modifyProcessModelPath(
      (processModelToUse as any).id
    );
    const processModelShowPath = `/process-models/${modifiedProcessModelId}`;
    console.log(`processModelShowPath: ${processModelShowPath}`);
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
