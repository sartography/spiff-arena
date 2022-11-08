import { useContext, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
// @ts-ignore
import { Add, Upload } from '@carbon/icons-react';
import {
  Accordion,
  AccordionItem,
  Dropdown,
  Button,
  Stack,
  ButtonSet,
  Modal,
  FileUploader,
  Table,
  TableHead,
  TableHeader,
  TableRow,
  TableCell,
  TableBody,
  // @ts-ignore
} from '@carbon/react';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import HttpService from '../services/HttpService';
import ErrorContext from '../contexts/ErrorContext';
import { ProcessFile, ProcessModel, RecentProcessModel } from '../interfaces';

interface ProcessModelFileCarbonDropdownItem {
  label: string;
  action: string;
  processModelFile: ProcessFile;
}

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

  const [processModel, setProcessModel] = useState<ProcessModel | null>(null);
  const [processInstanceResult, setProcessInstanceResult] = useState(null);
  const [reloadModel, setReloadModel] = useState<boolean>(false);
  const [filesToUpload, setFilesToUpload] = useState<any>(null);
  const [showFileUploadModal, setShowFileUploadModal] =
    useState<boolean>(false);

  useEffect(() => {
    const processResult = (result: ProcessModel) => {
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
    setErrorMessage(null);
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

  const processInstanceResultTag = () => {
    if (processModel && processInstanceResult) {
      let takeMeToMyTaskBlurb = null;
      // FIXME: ensure that the task is actually for the current user as well
      const processInstanceId = (processInstanceResult as any).id;
      const nextTask = (processInstanceResult as any).next_task;
      if (nextTask && nextTask.state === 'READY') {
        takeMeToMyTaskBlurb = (
          <span>
            You have a task to complete. Go to{' '}
            <Link to={`/tasks/${processInstanceId}/${nextTask.id}`}>
              my task
            </Link>
            .
          </span>
        );
      }
      return (
        <div className="alert alert-success" role="alert">
          <p>
            Process Instance {processInstanceId} kicked off (
            <Link
              to={`/admin/process-models/${processModel.process_group_id}/${processModel.id}/process-instances/${processInstanceId}`}
              data-qa="process-instance-show-link"
            >
              view
            </Link>
            ). {takeMeToMyTaskBlurb}
          </p>
        </div>
      );
    }
    return null;
  };

  const onUploadedCallback = () => {
    setReloadModel(true);
  };

  // Remove this code from
  const onDeleteFile = (fileName: string) => {
    const url = `/process-models/${params.process_group_id}/${params.process_model_id}/files/${fileName}`;
    const httpMethod = 'DELETE';
    const reloadModelOhYeah = (_httpResult: any) => {
      setReloadModel(!reloadModel);
    };
    HttpService.makeCallToBackend({
      path: url,
      successCallback: reloadModelOhYeah,
      httpMethod,
    });
  };

  const onProcessModelFileAction = (selection: any) => {
    const { selectedItem } = selection;
    if (selectedItem.action === 'delete') {
      onDeleteFile(selectedItem.processModelFile.name);
    }
  };

  const processModelFileList = () => {
    if (!processModel) {
      return null;
    }
    let constructedTag;
    const tags = processModel.files.map(
      (processModelFile: any, index: number) => {
        const isPrimaryBpmnFile =
          processModelFile.name === processModel.primary_file_name;
        const items: ProcessModelFileCarbonDropdownItem[] = [
          {
            label: 'Delete',
            action: 'delete',
            processModelFile,
          },
        ];
        if (processModelFile.name.match(/\.bpmn$/) && !isPrimaryBpmnFile) {
          items.push({
            label: 'Mark as Primary',
            action: 'mark_as_primary',
            processModelFile,
          });
        }

        let actionDropDirection = 'bottom';
        if (index + 1 === processModel.files.length) {
          actionDropDirection = 'top';
        }

        // The dropdown will get covered up if it extends passed the table container.
        // Using bottom direction at least gives a scrollbar so use that and hopefully
        // carbon will give access to z-index at some point.
        // https://github.com/carbon-design-system/carbon-addons-iot-react/issues/1487
        const actionsTableCell = (
          <TableCell key={`${processModelFile.name}-cell`}>
            <Dropdown
              id="default"
              direction={actionDropDirection}
              label="Select an action"
              onChange={(e: any) => {
                onProcessModelFileAction(e);
              }}
              items={items}
              itemToString={(item: ProcessModelFileCarbonDropdownItem) =>
                item ? item.label : ''
              }
            />
          </TableCell>
        );

        if (processModelFile.name.match(/\.(dmn|bpmn)$/)) {
          let primarySuffix = '';
          if (isPrimaryBpmnFile) {
            primarySuffix = '- Primary File';
          }
          constructedTag = (
            <TableRow key={processModelFile.name}>
              <TableCell key={`${processModelFile.name}-cell`}>
                <Link
                  to={`/admin/process-models/${processModel.process_group_id}/${processModel.id}/files/${processModelFile.name}`}
                >
                  {processModelFile.name}
                </Link>
                {primarySuffix}
              </TableCell>
              {actionsTableCell}
            </TableRow>
          );
        } else if (processModelFile.name.match(/\.(json|md)$/)) {
          constructedTag = (
            <TableRow key={processModelFile.name}>
              <TableCell key={`${processModelFile.name}-cell`}>
                <Link
                  to={`/admin/process-models/${processModel.process_group_id}/${processModel.id}/form/${processModelFile.name}`}
                >
                  {processModelFile.name}
                </Link>
              </TableCell>
              {actionsTableCell}
            </TableRow>
          );
        } else {
          constructedTag = (
            <TableRow key={processModelFile.name}>
              <TableCell key={`${processModelFile.name}-cell`}>
                {processModelFile.name}
              </TableCell>
            </TableRow>
          );
        }
        return constructedTag;
      }
    );

    // return <ul>{tags}</ul>;
    const headers = ['Name', 'Actions'];
    return (
      <Table size="lg" useZebraStyles={false}>
        <TableHead>
          <TableRow>
            {headers.map((header) => (
              <TableHeader id={header} key={header}>
                {header}
              </TableHeader>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>{tags}</TableBody>
      </Table>
    );
  };

  const processInstancesUl = () => {
    if (!processModel) {
      return null;
    }
    return (
      <ul>
        <li>
          <Link
            to={`/admin/process-instances?process_group_identifier=${processModel.process_group_id}&process_model_identifier=${processModel.id}`}
            data-qa="process-instance-list-link"
          >
            List
          </Link>
        </li>
        <li>
          <Link
            to={`/admin/process-models/${processModel.process_group_id}/${processModel.id}/process-instances/reports`}
            data-qa="process-instance-reports-link"
          >
            Reports
          </Link>
        </li>
      </ul>
    );
  };

  const handleFileUploadCancel = () => {
    setShowFileUploadModal(false);
  };

  const handleFileUpload = (event: any) => {
    if (processModel) {
      event.preventDefault();
      const url = `/process-models/${processModel.process_group_id}/${processModel.id}/files`;
      const formData = new FormData();
      formData.append('file', filesToUpload[0]);
      formData.append('fileName', filesToUpload[0].name);
      HttpService.makeCallToBackend({
        path: url,
        successCallback: onUploadedCallback,
        httpMethod: 'POST',
        postBody: formData,
      });
      setShowFileUploadModal(false);
    }
  };

  const fileUploadModal = () => {
    return (
      <Modal
        open={showFileUploadModal}
        modalHeading="Upload File"
        primaryButtonText="Upload"
        secondaryButtonText="Cancel"
        onSecondarySubmit={handleFileUploadCancel}
        onRequestClose={handleFileUploadCancel}
        onRequestSubmit={handleFileUpload}
      >
        <FileUploader
          labelTitle="Upload files"
          labelDescription="Max file size is 500mb. Only .bpmn, .dmn, and .json files are supported."
          buttonLabel="Add file"
          buttonKind="primary"
          size="md"
          filenameStatus="edit"
          role="button"
          accept={['.bpmn', '.dmn', '.json']}
          disabled={false}
          iconDescription="Delete file"
          name=""
          multiple={false}
          onChange={(event: any) => setFilesToUpload(event.target.files)}
        />
      </Modal>
    );
  };

  const processModelButtons = () => {
    if (!processModel) {
      return null;
    }
    return (
      <Accordion>
        <AccordionItem
          title={
            <Stack orientation="horizontal">
              <span>
                <Button size="sm" kind="ghost">
                  Files
                </Button>
              </span>
            </Stack>
          }
        >
          <ButtonSet>
            <Button
              renderIcon={Upload}
              onClick={() => setShowFileUploadModal(true)}
              size="sm"
              kind=""
              className="button-white-background"
            >
              Upload File
            </Button>
            <Button
              renderIcon={Add}
              href={`/admin/process-models/${processModel.process_group_id}/${processModel.id}/files?file_type=dmn`}
              size="sm"
            >
              New DMN File
            </Button>
            <Button
              renderIcon={Add}
              href={`/admin/process-models/${processModel.process_group_id}/${processModel.id}/form?file_ext=json`}
              size="sm"
            >
              New JSON File
            </Button>
            <Button
              renderIcon={Add}
              href={`/admin/process-models/${processModel.process_group_id}/${processModel.id}/form?file_ext=md`}
              size="sm"
            >
              New Markdown File
            </Button>
          </ButtonSet>
          <br />
          {processModelFileList()}
        </AccordionItem>
      </Accordion>
    );
  };

  if (processModel) {
    return (
      <>
        <ProcessBreadcrumb
          processGroupId={processModel.process_group_id}
          processModelId={processModel.id}
        />
        <h1>{processModel.display_name}</h1>
        <p>{processModel.description}</p>
        <Stack orientation="horizontal" gap={3}>
          <Button onClick={processInstanceCreateAndRun} variant="primary">
            Run
          </Button>
          <Button
            href={`/admin/process-models/${processModel.process_group_id}/${processModel.id}/edit`}
            variant="secondary"
          >
            Edit process model
          </Button>
        </Stack>
        {fileUploadModal()}
        {processInstanceResultTag()}
        <br />
        {processModelButtons()}
        <br />
        <br />
        <h3>Process Instances</h3>
        {processInstancesUl()}
      </>
    );
  }
  return null;
}
