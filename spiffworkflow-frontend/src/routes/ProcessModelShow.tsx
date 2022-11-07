import { useContext, useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
// @ts-ignore
import { Add, Upload } from '@carbon/icons-react';
import {
  Accordion,
  AccordionItem,
  Grid,
  Column,
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
import FileInput from '../components/FileInput';
import HttpService from '../services/HttpService';
import ErrorContext from '../contexts/ErrorContext';
import { ProcessModel, RecentProcessModel } from '../interfaces';

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
  const navigate = useNavigate();

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
              to={`/admin/process-models/${processModel.process_group_id}/${
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
    return null;
  };

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
          <TableRow key={processModelFile.name}>
            <TableCell key={`${processModelFile.name}-cell`}>
              <Link
                to={`/admin/process-models/${
                  (processModel as any).process_group_id
                }/${(processModel as any).id}/files/${processModelFile.name}`}
              >
                {processModelFile.name}
              </Link>
              {primarySuffix}
            </TableCell>
          </TableRow>
        );
      } else if (processModelFile.name.match(/\.(json|md)$/)) {
        constructedTag = (
          <TableRow key={processModelFile.name}>
            <TableCell key={`${processModelFile.name}-cell`}>
              <Link
                to={`/admin/process-models/${
                  (processModel as any).process_group_id
                }/${(processModel as any).id}/form/${processModelFile.name}`}
              >
                {processModelFile.name}
              </Link>
            </TableCell>
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
    });

    // return <ul>{tags}</ul>;
    const headers = ['name', 'Actions'];
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

  const handleFileUploadCancel = () => {
    setShowFileUploadModal(false);
  };

  const handleFileUpload = (event: any) => {
    event.preventDefault();
    const url = `/process-models/${(processModel as any).process_group_id}/${
      (processModel as any).id
    }/files`;
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
              href={`/admin/process-models/${
                (processModel as any).process_group_id
              }/${(processModel as any).id}/files?file_type=dmn`}
              size="sm"
            >
              New DMN File
            </Button>
            <Button
              renderIcon={Add}
              href={`/admin/process-models/${
                (processModel as any).process_group_id
              }/${(processModel as any).id}/form?file_ext=json`}
              size="sm"
            >
              New JSON File
            </Button>
            <Button
              renderIcon={Add}
              href={`/admin/process-models/${
                (processModel as any).process_group_id
              }/${(processModel as any).id}/form?file_ext=md`}
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
