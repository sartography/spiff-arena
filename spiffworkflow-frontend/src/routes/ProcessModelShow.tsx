import { useContext, useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import {
  Add,
  Upload,
  Download,
  TrashCan,
  Favorite,
  Edit,
  // @ts-ignore
} from '@carbon/icons-react';
import {
  Accordion,
  AccordionItem,
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
import { modifyProcessModelPath, unModifyProcessModelPath } from '../helpers';
import { ProcessFile, ProcessModel, RecentProcessModel } from '../interfaces';
import ButtonWithConfirmation from '../components/ButtonWithConfirmation';

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

  const modifiedProcessModelId = modifyProcessModelPath(
    `${params.process_model_id}`
  );

  useEffect(() => {
    const processResult = (result: ProcessModel) => {
      setProcessModel(result);
      setReloadModel(false);
      storeRecentProcessModelInLocalStorage(result, params);
    };
    HttpService.makeCallToBackend({
      path: `/process-models/${modifiedProcessModelId}`,
      successCallback: processResult,
    });
  }, [params, reloadModel, modifiedProcessModelId]);

  const processModelRun = (processInstance: any) => {
    setErrorMessage(null);
    HttpService.makeCallToBackend({
      path: `/process-instances/${processInstance.id}/run`,
      successCallback: setProcessInstanceResult,
      failureCallback: setErrorMessage,
      httpMethod: 'POST',
    });
  };

  const processInstanceCreateAndRun = () => {
    HttpService.makeCallToBackend({
      path: `/process-models/${modifiedProcessModelId}/process-instances`,
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
              to={`/admin/process-models/${modifiedProcessModelId}/process-instances/${processInstanceId}`}
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
  const reloadModelOhYeah = (_httpResult: any) => {
    setReloadModel(!reloadModel);
  };

  // Remove this code from
  const onDeleteFile = (fileName: string) => {
    const url = `/process-models/${modifiedProcessModelId}/files/${fileName}`;
    const httpMethod = 'DELETE';
    HttpService.makeCallToBackend({
      path: url,
      successCallback: reloadModelOhYeah,
      httpMethod,
    });
  };

  const onSetPrimaryFile = (fileName: string) => {
    const url = `/process-models/${modifiedProcessModelId}`;
    const httpMethod = 'PUT';

    const processModelToPass = {
      primary_file_name: fileName,
    };
    HttpService.makeCallToBackend({
      path: url,
      successCallback: onUploadedCallback,
      httpMethod,
      postBody: processModelToPass,
    });
  };
  const handleProcessModelFileResult = (processModelFile: ProcessFile) => {
    if (
      !('file_contents' in processModelFile) ||
      processModelFile.file_contents === undefined
    ) {
      setErrorMessage({
        message: `Could not file file contents for file: ${processModelFile.name}`,
      });
      return;
    }
    let contentType = 'application/xml';
    if (processModelFile.type === 'json') {
      contentType = 'application/json';
    }
    const element = document.createElement('a');
    const file = new Blob([processModelFile.file_contents], {
      type: contentType,
    });
    const downloadFileName = processModelFile.name;
    element.href = URL.createObjectURL(file);
    element.download = downloadFileName;
    document.body.appendChild(element);
    element.click();
  };

  const downloadFile = (fileName: string) => {
    setErrorMessage(null);
    const processModelPath = `process-models/${modifiedProcessModelId}`;
    HttpService.makeCallToBackend({
      path: `/${processModelPath}/files/${fileName}`,
      successCallback: handleProcessModelFileResult,
    });
  };

  const navigateToFileEdit = (processModelFile: ProcessFile) => {
    if (processModel) {
      if (processModelFile.name.match(/\.(dmn|bpmn)$/)) {
        navigate(
          `/admin/process-models/${modifiedProcessModelId}/files/${processModelFile.name}`
        );
      } else if (processModelFile.name.match(/\.(json|md)$/)) {
        navigate(
          `/admin/process-models/${modifiedProcessModelId}/form/${processModelFile.name}`
        );
      }
    }
  };

  const renderButtonElements = (
    processModelFile: ProcessFile,
    isPrimaryBpmnFile: boolean
  ) => {
    const elements = [];
    elements.push(
      <Button
        kind="ghost"
        renderIcon={Edit}
        iconDescription="Edit File"
        hasIconOnly
        size="lg"
        data-qa={`edit-file-${processModelFile.name.replace('.', '-')}`}
        onClick={() => navigateToFileEdit(processModelFile)}
      />
    );
    elements.push(
      <Button
        kind="ghost"
        renderIcon={Download}
        iconDescription="Download File"
        hasIconOnly
        size="lg"
        onClick={() => downloadFile(processModelFile.name)}
      />
    );

    elements.push(
      <ButtonWithConfirmation
        kind="ghost"
        renderIcon={TrashCan}
        iconDescription="Delete File"
        hasIconOnly
        description={`Delete file: ${processModelFile.name}`}
        onConfirmation={() => {
          onDeleteFile(processModelFile.name);
        }}
        confirmButtonLabel="Delete"
      />
    );
    if (processModelFile.name.match(/\.bpmn$/) && !isPrimaryBpmnFile) {
      elements.push(
        <Button
          kind="ghost"
          renderIcon={Favorite}
          iconDescription="Set As Primary File"
          hasIconOnly
          size="lg"
          onClick={() => onSetPrimaryFile(processModelFile.name)}
        />
      );
    }
    return elements;
  };

  const processModelFileList = () => {
    if (!processModel) {
      return null;
    }
    let constructedTag;
    const tags = processModel.files.map((processModelFile: ProcessFile) => {
      const isPrimaryBpmnFile =
        processModelFile.name === processModel.primary_file_name;

      let actionsTableCell = null;
      if (processModelFile.name.match(/\.(dmn|bpmn|json|md)$/)) {
        actionsTableCell = (
          <TableCell key={`${processModelFile.name}-cell`}>
            {renderButtonElements(processModelFile, isPrimaryBpmnFile)}
          </TableCell>
        );
      }

      let primarySuffix = '';
      if (isPrimaryBpmnFile) {
        primarySuffix = '- Primary File';
      }
      constructedTag = (
        <TableRow key={processModelFile.name}>
          <TableCell key={`${processModelFile.name}-cell`}>
            {processModelFile.name}
            {primarySuffix}
          </TableCell>
          {actionsTableCell}
        </TableRow>
      );
      return constructedTag;
    });

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
    const unmodifiedProcessModelId: String = unModifyProcessModelPath(
      `${params.process_model_id}`
    );
    if (!processModel) {
      return null;
    }
    return (
      <ul>
        <li>
          <Link
            to={`/admin/process-instances?process_model_identifier=${unmodifiedProcessModelId}`}
            data-qa="process-instance-list-link"
          >
            List
          </Link>
        </li>
        <li>
          <Link
            to={`/admin/process-models/${modifiedProcessModelId}/process-instances/reports`}
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
      const url = `/process-models/${modifiedProcessModelId}/files`;
      const formData = new FormData();
      formData.append('file', filesToUpload[0]);
      formData.append('fileName', filesToUpload[0].name);
      HttpService.makeCallToBackend({
        path: url,
        successCallback: onUploadedCallback,
        httpMethod: 'POST',
        postBody: formData,
      });
    }
    setShowFileUploadModal(false);
  };

  const fileUploadModal = () => {
    return (
      <Modal
        data-qa="modal-upload-file-dialog"
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
          data-qa="files-accordion"
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
              data-qa="upload-file-button"
              onClick={() => setShowFileUploadModal(true)}
              size="sm"
              kind=""
              className="button-white-background"
            >
              Upload File
            </Button>
            <Button
              renderIcon={Add}
              href={`/admin/process-models/${modifiedProcessModelId}/files?file_type=bpmn`}
              size="sm"
            >
              New BPMN File
            </Button>
            <Button
              renderIcon={Add}
              href={`/admin/process-models/${modifiedProcessModelId}/files?file_type=dmn`}
              size="sm"
            >
              New DMN File
            </Button>
            <Button
              renderIcon={Add}
              href={`/admin/process-models/${modifiedProcessModelId}/form?file_ext=json`}
              size="sm"
            >
              New JSON File
            </Button>
            <Button
              renderIcon={Add}
              href={`/admin/process-models/${modifiedProcessModelId}/form?file_ext=md`}
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
        {fileUploadModal()}
        <ProcessBreadcrumb
          hotCrumbs={[
            ['Process Groups', '/admin'],
            [
              `Process Model: ${processModel.id}`,
              `process_model:${processModel.id}`,
            ],
          ]}
        />
        <h1>Process Model: {processModel.display_name}</h1>
        <p className="process-description">{processModel.description}</p>
        <Stack orientation="horizontal" gap={3}>
          <Button onClick={processInstanceCreateAndRun} variant="primary">
            Run
          </Button>
          <Button
            href={`/admin/process-models/${modifiedProcessModelId}/edit`}
            variant="secondary"
          >
            Edit process model
          </Button>
        </Stack>
        <br />
        <br />
        {processInstanceResultTag()}
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
