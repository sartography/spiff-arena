import { useContext, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Button, Stack } from 'react-bootstrap';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import FileInput from '../components/FileInput';
import HttpService from '../services/HttpService';
import ErrorContext from '../contexts/ErrorContext';
import { RecentProcessModel } from '../interfaces';

const storeRecentProcessModelInLocalStorage = (
  processModelForStorage: any,
  params: any
) => {
  if (
    params.process_group_id === undefined ||
    params.process_model_id === undefined
  ) {
    return;
  }
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
    processGroupIdentifier: processModelForStorage.process_group_id,
    processModelIdentifier: processModelForStorage.id,
    processModelDisplayName: processModelForStorage.display_name,
  };

  // If our parsed/empty array doesn't already have this value in it...
  const matchingItem = array.find(
    (item) =>
      item.processGroupIdentifier === value.processGroupIdentifier &&
      item.processModelIdentifier === value.processModelIdentifier
  );
  if (matchingItem === undefined) {
    // add the value to the beginning of the array
    array.unshift(value);

    // Keep the array to 3 items
    if (array.length > 3) {
      array.pop();
    }

    // turn the array WITH THE NEW VALUE IN IT into a string to prepare it to be stored in localStorage
    const stringRepresentingArray = JSON.stringify(array);

    // and store it in localStorage as "recentProcessModels"
    window.localStorage.setItem('recentProcessModels', stringRepresentingArray);
  }
};

export default function ProcessModelShow() {
  const params = useParams();
  const setErrorMessage = (useContext as any)(ErrorContext)[1];

  const [processModel, setProcessModel] = useState({});
  const [processInstanceResult, setProcessInstanceResult] = useState(null);
  const [reloadModel, setReloadModel] = useState(false);

  useEffect(() => {
    const processResult = (result: object) => {
      setProcessModel(result);
      setReloadModel(false);
      storeRecentProcessModelInLocalStorage(result, params);
    };
    HttpService.makeCallToBackend({
      path: `/process-models/${params.process_group_id}/${params.process_model_id}`,
      successCallback: processResult,
    });
  }, [params, reloadModel]);

  const processModelRun = (processInstance: any) => {
    setErrorMessage('');
    HttpService.makeCallToBackend({
      path: `/process-models/${params.process_group_id}/${params.process_model_id}/process-instances/${processInstance.id}/run`,
      successCallback: setProcessInstanceResult,
      failureCallback: setErrorMessage,
      httpMethod: 'POST',
    });
  };

  const processInstanceCreateAndRun = () => {
    HttpService.makeCallToBackend({
      path: `/process-models/${params.process_group_id}/${params.process_model_id}/process-instances`,
      successCallback: processModelRun,
      httpMethod: 'POST',
    });
  };

  let processInstanceResultTag = null;
  if (processInstanceResult) {
    let takeMeToMyTaskBlurb = null;
    // FIXME: ensure that the task is actually for the current user as well
    const processInstanceId = (processInstanceResult as any).id;
    const nextTask = (processInstanceResult as any).next_task;
    if (nextTask && nextTask.state === 'READY') {
      takeMeToMyTaskBlurb = (
        <span>
          You have a task to complete. Go to{' '}
          <Link to={`/tasks/${processInstanceId}/${nextTask.id}`}>my task</Link>
          .
        </span>
      );
    }
    processInstanceResultTag = (
      <div className="alert alert-success" role="alert">
        <p>
          Process Instance {processInstanceId} kicked off (
          <Link
            to={`/admin/process-models/${
              (processModel as any).process_group_id
            }/${
              (processModel as any).id
            }/process-instances/${processInstanceId}`}
            data-qa="process-instance-show-link"
          >
            view
          </Link>
          ). {takeMeToMyTaskBlurb}
        </p>
      </div>
    );
  }

  const onUploadedCallback = () => {
    setReloadModel(true);
  };

  const processModelFileList = () => {
    let constructedTag;
    const tags = (processModel as any).files.map((processModelFile: any) => {
      if (processModelFile.name.match(/\.(dmn|bpmn)$/)) {
        let primarySuffix = '';
        if (processModelFile.name === (processModel as any).primary_file_name) {
          primarySuffix = '- Primary File';
        }
        constructedTag = (
          <li key={processModelFile.name}>
            <Link
              to={`/admin/process-models/${
                (processModel as any).process_group_id
              }/${(processModel as any).id}/files/${processModelFile.name}`}
            >
              {processModelFile.name}
            </Link>
            {primarySuffix}
          </li>
        );
      } else if (processModelFile.name.match(/\.(json|md)$/)) {
        constructedTag = (
          <li key={processModelFile.name}>
            <Link
              to={`/admin/process-models/${
                (processModel as any).process_group_id
              }/${(processModel as any).id}/form/${processModelFile.name}`}
            >
              {processModelFile.name}
            </Link>
          </li>
        );
      } else {
        constructedTag = (
          <li key={processModelFile.name}>{processModelFile.name}</li>
        );
      }
      return constructedTag;
    });

    return <ul>{tags}</ul>;
  };

  const processInstancesUl = () => {
    return (
      <ul>
        <li>
          <Link
            to={`/admin/process-instances?process_group_identifier=${
              (processModel as any).process_group_id
            }&process_model_identifier=${(processModel as any).id}`}
            data-qa="process-instance-list-link"
          >
            List
          </Link>
        </li>
        <li>
          <Link
            to={`/admin/process-models/${
              (processModel as any).process_group_id
            }/${(processModel as any).id}/process-instances/reports`}
            data-qa="process-instance-reports-link"
          >
            Reports
          </Link>
        </li>
      </ul>
    );
  };

  const processModelButtons = () => {
    return (
      <Stack direction="horizontal" gap={3}>
        <Button onClick={processInstanceCreateAndRun} variant="primary">
          Run
        </Button>
        <Button
          href={`/admin/process-models/${
            (processModel as any).process_group_id
          }/${(processModel as any).id}/edit`}
          variant="secondary"
        >
          Edit process model
        </Button>
        <Button
          href={`/admin/process-models/${
            (processModel as any).process_group_id
          }/${(processModel as any).id}/files?file_type=bpmn`}
          variant="warning"
        >
          Add New BPMN File
        </Button>
        <Button
          href={`/admin/process-models/${
            (processModel as any).process_group_id
          }/${(processModel as any).id}/files?file_type=dmn`}
          variant="success"
        >
          Add New DMN File
        </Button>
        <Button
          href={`/admin/process-models/${
            (processModel as any).process_group_id
          }/${(processModel as any).id}/form?file_ext=json`}
          variant="info"
        >
          Add New JSON File
        </Button>
        <Button
          href={`/admin/process-models/${
            (processModel as any).process_group_id
          }/${(processModel as any).id}/form?file_ext=md`}
          variant="info"
        >
          Add New Markdown File
        </Button>
      </Stack>
    );
  };

  if (Object.keys(processModel).length > 1) {
    return (
      <>
        <ProcessBreadcrumb
          processGroupId={(processModel as any).process_group_id}
          processModelId={(processModel as any).id}
        />
        {processInstanceResultTag}
        <FileInput
          processModelId={(processModel as any).id}
          processGroupId={(processModel as any).process_group_id}
          onUploadedCallback={onUploadedCallback}
        />
        <br />
        {processModelButtons()}
        <br />
        <br />
        <h3>Process Instances</h3>
        {processInstancesUl()}
        <br />
        <br />
        <h3>Files</h3>
        {processModelFileList()}
      </>
    );
  }
  return null;
}
