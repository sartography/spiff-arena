import { useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button,
  // @ts-ignore
} from '@carbon/react';
import { Can } from '@casl/react';
import {
  PermissionsToCheck,
  ProcessModel,
  RecentProcessModel,
} from '../interfaces';
import HttpService from '../services/HttpService';
import ErrorContext from '../contexts/ErrorContext';
import { modifyProcessIdentifierForPathParam } from '../helpers';
import { usePermissionFetcher } from '../hooks/PermissionService';

const storeRecentProcessModelInLocalStorage = (
  processModelForStorage: ProcessModel
) => {
  // All values stored in localStorage are strings.
  // Grab our recentProcessModels string from localStorage.
  const stringFromLocalStorage = window.localStorage.getItem(
    'recentProcessModels'
  );

  // adapted from https://stackoverflow.com/a/59424458/6090676
  // If that value is null (meaning that we've never saved anything to that spot in localStorage before), use an empty array as our array. Otherwise, use the value we parse out.
  let array: RecentProcessModel[] = [];
  if (stringFromLocalStorage !== null) {
    // Then parse that string into an actual value.
    array = JSON.parse(stringFromLocalStorage);
  }

  // Here's the value we want to add
  const value = {
    processModelIdentifier: processModelForStorage.id,
    processModelDisplayName: processModelForStorage.display_name,
  };

  // anything with a processGroupIdentifier is old and busted. leave it behind.
  array = array.filter((item) => item.processGroupIdentifier === undefined);

  // If our parsed/empty array doesn't already have this value in it...
  const matchingItem = array.find(
    (item) => item.processModelIdentifier === value.processModelIdentifier
  );
  if (matchingItem === undefined) {
    // add the value to the beginning of the array
    array.unshift(value);

    // Keep the array to 3 items
    if (array.length > 3) {
      array.pop();
    }
  }

  // once the old and busted serializations are gone, we can put these two statements inside the above if statement

  // turn the array WITH THE NEW VALUE IN IT into a string to prepare it to be stored in localStorage
  const stringRepresentingArray = JSON.stringify(array);

  // and store it in localStorage as "recentProcessModels"
  window.localStorage.setItem('recentProcessModels', stringRepresentingArray);
};

type OwnProps = {
  processModel: ProcessModel;
  onSuccessCallback: Function;
  className?: string;
};

export default function ProcessInstanceRun({
  processModel,
  onSuccessCallback,
  className,
}: OwnProps) {
  const navigate = useNavigate();
  const setErrorMessage = (useContext as any)(ErrorContext)[1];
  const modifiedProcessModelId = modifyProcessIdentifierForPathParam(
    processModel.id
  );

  const processInstanceActionPath = `/v1.0/process-models/${modifiedProcessModelId}/process-instances`;
  const permissionRequestData: PermissionsToCheck = {
    [processInstanceActionPath]: ['POST'],
  };
  const { ability } = usePermissionFetcher(permissionRequestData);

  const onProcessInstanceRun = (processInstance: any) => {
    // FIXME: ensure that the task is actually for the current user as well
    const processInstanceId = (processInstance as any).id;
    const nextTask = (processInstance as any).next_task;
    if (nextTask && nextTask.state === 'READY') {
      navigate(`/tasks/${processInstanceId}/${nextTask.id}`);
    }
    onSuccessCallback(processInstance);
  };

  const processModelRun = (processInstance: any) => {
    setErrorMessage(null);
    storeRecentProcessModelInLocalStorage(processModel);
    HttpService.makeCallToBackend({
      path: `/process-instances/${modifiedProcessModelId}/${processInstance.id}/run`,
      successCallback: onProcessInstanceRun,
      failureCallback: setErrorMessage,
      httpMethod: 'POST',
    });
  };

  const processInstanceCreateAndRun = () => {
    HttpService.makeCallToBackend({
      path: processInstanceActionPath,
      successCallback: processModelRun,
      httpMethod: 'POST',
    });
  };

  return (
    <Can I="POST" a={processInstanceActionPath} ability={ability}>
      <Button onClick={processInstanceCreateAndRun} className={className}>
        Run
      </Button>
    </Can>
  );
}
