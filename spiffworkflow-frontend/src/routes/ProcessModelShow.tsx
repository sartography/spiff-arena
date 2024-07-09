import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import {
  Download,
  Edit,
  Favorite,
  TrashCan,
  Upload,
  View,
} from '@carbon/icons-react';
import {
  Button,
  Column,
  Dropdown,
  FileUploader,
  Grid,
  Modal,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Tabs,
  Tab,
  TabList,
  TabPanels,
  TabPanel,
} from '@carbon/react';
import { Can } from '@casl/react';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import HttpService from '../services/HttpService';
import useAPIError from '../hooks/UseApiError';

import {
  getGroupFromModifiedModelId,
  modifyProcessIdentifierForPathParam,
  setPageTitle,
} from '../helpers';
import { PermissionsToCheck, ProcessFile, ProcessModel } from '../interfaces';
import ButtonWithConfirmation from '../components/ButtonWithConfirmation';
import { usePermissionFetcher } from '../hooks/PermissionService';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import ProcessInstanceRun from '../components/ProcessInstanceRun';
import { Notification } from '../components/Notification';
import ProcessModelTestRun from '../components/ProcessModelTestRun';
import MarkdownDisplayForFile from '../components/MarkdownDisplayForFile';
import ProcessInstanceListTable from '../components/ProcessInstanceListTable';

export default function ProcessModelShow() {
  const params = useParams();
  const { addError, removeError } = useAPIError();
  const navigate = useNavigate();

  const [processModel, setProcessModel] = useState<ProcessModel | null>(null);
  const [reloadModel, setReloadModel] = useState<boolean>(false);
  const [filesToUpload, setFilesToUpload] = useState<any>(null);
  const [showFileUploadModal, setShowFileUploadModal] =
    useState<boolean>(false);
  const [processModelPublished, setProcessModelPublished] = useState<any>(null);
  const [publishDisabled, setPublishDisabled] = useState<boolean>(false);
  const [selectedTabIndex, setSelectedTabIndex] = useState<number>(0);
  const [readmeFile, setReadmeFile] = useState<ProcessFile | null>(null);

  const { targetUris } = useUriListForPermissions();
  const permissionRequestData: PermissionsToCheck = {
    [targetUris.processInstanceCreatePath]: ['POST'],
    [targetUris.processInstanceListForMePath]: ['POST'],
    [targetUris.processModelFileCreatePath]: ['POST', 'PUT', 'GET', 'DELETE'],
    [targetUris.processModelPublishPath]: ['POST'],
    [targetUris.processModelShowPath]: ['PUT', 'DELETE'],
    [targetUris.processModelTestsPath]: ['POST'],
  };
  const { ability, permissionsLoaded } = usePermissionFetcher(
    permissionRequestData,
  );

  const modifiedProcessModelId = modifyProcessIdentifierForPathParam(
    `${params.process_model_id}`,
  );

  let hasTestCaseFiles: boolean = false;

  const isTestCaseFile = (processModelFile: ProcessFile) => {
    return processModelFile.name.match(/^test_.*\.json$/);
  };

  if (processModel) {
    hasTestCaseFiles = !!processModel.files.find(
      (processModelFile: ProcessFile) => isTestCaseFile(processModelFile),
    );
  }

  useEffect(() => {
    const processResult = (result: ProcessModel) => {
      setProcessModel(result);
      setReloadModel(false);
      setPageTitle([result.display_name]);

      let newTabIndex = 1;
      result.files.forEach((file: ProcessFile) => {
        if (file.name === 'README.md') {
          setReadmeFile(file);
          newTabIndex = 0;
        }
      });
      setSelectedTabIndex(newTabIndex);
    };
    HttpService.makeCallToBackend({
      path: `/process-models/${modifiedProcessModelId}?include_file_references=true`,
      successCallback: processResult,
    });
  }, [reloadModel, modifiedProcessModelId]);

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
      addError({
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
    removeError();
    const processModelPath = `process-models/${modifiedProcessModelId}`;
    HttpService.makeCallToBackend({
      path: `/${processModelPath}/files/${fileName}`,
      successCallback: handleProcessModelFileResult,
    });
  };

  const profileModelFileEditUrl = (processModelFile: ProcessFile) => {
    if (processModel) {
      if (processModelFile.name.match(/\.(dmn|bpmn)$/)) {
        return `/editor/process-models/${modifiedProcessModelId}/files/${processModelFile.name}`;
      }
      if (processModelFile.name.match(/\.(json|md)$/)) {
        return `/process-models/${modifiedProcessModelId}/form/${processModelFile.name}`;
      }
    }
    return null;
  };

  const navigateToProcessModels = (_result: any) => {
    navigate(
      `/process-groups/${getGroupFromModifiedModelId(modifiedProcessModelId)}`,
    );
  };

  const deleteProcessModel = () => {
    HttpService.makeCallToBackend({
      path: `/process-models/${modifiedProcessModelId}`,
      successCallback: navigateToProcessModels,
      httpMethod: 'DELETE',
    });
  };

  const postPublish = (value: any) => {
    setPublishDisabled(false);
    setProcessModelPublished(value);
  };

  const publishProcessModel = () => {
    setPublishDisabled(true);
    setProcessModelPublished(null);
    HttpService.makeCallToBackend({
      path: targetUris.processModelPublishPath,
      successCallback: postPublish,
      httpMethod: 'POST',
    });
  };

  const navigateToFileEdit = (processModelFile: ProcessFile) => {
    const url = profileModelFileEditUrl(processModelFile);
    if (url) {
      navigate(url);
    }
  };

  const renderButtonElements = (
    processModelFile: ProcessFile,
    isPrimaryBpmnFile: boolean,
  ) => {
    const elements = [];

    // So there is a bug in here. Since we use a react context for error messages, and since
    // its provider wraps the entire app, child components will re-render when there is an
    // error displayed. This is normally fine, but it interacts badly with the casl ability.can
    // functionality. We have observed that permissionsLoaded is never set to false. So when
    // you run a process and it fails, for example, process model show will re-render, the ability
    // will be cleared out and it will start fetching permissions from the server, but this
    // component still thinks permissionsLoaded is telling the truth (it says true, but it's actually false).
    // The only bad effect that we know of is that the Edit icon becomes an eye icon even for admins.
    let icon = View;
    let actionWord = 'View';
    if (ability.can('PUT', targetUris.processModelFileCreatePath)) {
      icon = Edit;
      actionWord = 'Edit';
    }
    elements.push(
      <Can I="GET" a={targetUris.processModelFileCreatePath} ability={ability}>
        <Button
          kind="ghost"
          renderIcon={icon}
          iconDescription={`${actionWord} File`}
          hasIconOnly
          size="lg"
          data-qa={`edit-file-${processModelFile.name.replace('.', '-')}`}
          onClick={() => navigateToFileEdit(processModelFile)}
        />
      </Can>,
    );
    elements.push(
      <Can I="GET" a={targetUris.processModelFileCreatePath} ability={ability}>
        <Button
          kind="ghost"
          renderIcon={Download}
          iconDescription="Download File"
          hasIconOnly
          size="lg"
          onClick={() => downloadFile(processModelFile.name)}
        />
      </Can>,
    );

    if (!isPrimaryBpmnFile) {
      elements.push(
        <Can
          I="DELETE"
          a={targetUris.processModelFileCreatePath}
          ability={ability}
        >
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
            classNameForModal="modal-within-table-cell"
          />
        </Can>,
      );
    }
    if (processModelFile.name.match(/\.bpmn$/) && !isPrimaryBpmnFile) {
      elements.push(
        <Can I="PUT" a={targetUris.processModelShowPath} ability={ability}>
          <Button
            kind="ghost"
            renderIcon={Favorite}
            iconDescription="Set As Primary File"
            hasIconOnly
            size="lg"
            onClick={() => onSetPrimaryFile(processModelFile.name)}
          />
        </Can>,
      );
    }
    if (isTestCaseFile(processModelFile)) {
      elements.push(
        <Can I="POST" a={targetUris.processModelTestsPath} ability={ability}>
          <ProcessModelTestRun
            processModelFile={processModelFile}
            titleText="Run BPMN unit tests defined in this file"
            classNameForModal="modal-within-table-cell"
          />
        </Can>,
      );
    }
    return elements;
  };

  const processModelFileList = () => {
    if (!processModel || !permissionsLoaded) {
      return null;
    }
    let constructedTag;
    const tags = processModel.files
      .map((processModelFile: ProcessFile) => {
        if (!processModelFile.name.match(/\.(dmn|bpmn|json|md)$/)) {
          return undefined;
        }
        const isPrimaryBpmnFile =
          processModelFile.name === processModel.primary_file_name;

        let actionsTableCell = null;
        if (processModelFile.name.match(/\.(dmn|bpmn|json|md)$/)) {
          actionsTableCell = (
            <TableCell key={`${processModelFile.name}-action`} align="right">
              {renderButtonElements(processModelFile, isPrimaryBpmnFile)}
            </TableCell>
          );
        }

        let primarySuffix = null;
        if (isPrimaryBpmnFile) {
          primarySuffix = (
            <span>
              &nbsp;-{' '}
              <span className="primary-file-text-suffix">Primary File</span>
            </span>
          );
        }
        let fileLink = null;
        const fileUrl = profileModelFileEditUrl(processModelFile);
        if (fileUrl) {
          fileLink = <Link to={fileUrl}>{processModelFile.name}</Link>;
        }
        constructedTag = (
          <TableRow key={processModelFile.name}>
            <TableCell
              key={`${processModelFile.name}-cell`}
              className="process-model-file-table-filename"
              title={processModelFile.name}
            >
              {fileLink}
              {primarySuffix}
            </TableCell>
            {actionsTableCell}
          </TableRow>
        );
        return constructedTag;
      })
      .filter((element: any) => element !== undefined);

    if (tags.length > 0) {
      return (
        <Table
          size="lg"
          useZebraStyles={false}
          className="process-model-file-table"
        >
          <TableHead>
            <TableRow>
              <TableHeader id="Name" key="Name">
                Name
              </TableHeader>
              <TableHeader
                id="Actions"
                key="Actions"
                className="table-header-right-align"
              >
                Actions
              </TableHeader>
            </TableRow>
          </TableHead>
          <TableBody>{tags}</TableBody>
        </Table>
      );
    }
    return null;
  };

  const [fileUploadEvent, setFileUploadEvent] = useState(null);
  const [duplicateFilename, setDuplicateFilename] = useState<String>('');
  const [showOverwriteConfirmationPrompt, setShowOverwriteConfirmationPrompt] =
    useState(false);

  const doFileUpload = (event: any) => {
    event.preventDefault();
    removeError();
    const url = `/process-models/${modifiedProcessModelId}/files`;
    const formData = new FormData();
    formData.append('file', filesToUpload[0]);
    formData.append('fileName', filesToUpload[0].name);
    HttpService.makeCallToBackend({
      path: url,
      successCallback: onUploadedCallback,
      httpMethod: 'POST',
      postBody: formData,
      failureCallback: addError,
    });
    setFilesToUpload(null);
  };

  const handleFileUploadCancel = () => {
    setShowFileUploadModal(false);
    setFilesToUpload(null);
  };
  const handleOverwriteFileConfirm = () => {
    setShowOverwriteConfirmationPrompt(false);
    doFileUpload(fileUploadEvent);
  };
  const handleOverwriteFileCancel = () => {
    setShowOverwriteConfirmationPrompt(false);
    setFilesToUpload(null);
  };

  const confirmOverwriteFileDialog = () => {
    return (
      <Modal
        danger
        open={showOverwriteConfirmationPrompt}
        data-qa="file-overwrite-modal-confirmation-dialog"
        modalHeading={`Overwrite the file: ${duplicateFilename}`}
        modalLabel="Overwrite file?"
        primaryButtonText="Yes"
        secondaryButtonText="Cancel"
        onSecondarySubmit={handleOverwriteFileCancel}
        onRequestSubmit={handleOverwriteFileConfirm}
        onRequestClose={handleOverwriteFileCancel}
      />
    );
  };
  const displayOverwriteConfirmation = (filename: String) => {
    setDuplicateFilename(filename);
    setShowOverwriteConfirmationPrompt(true);
  };

  const checkDuplicateFile = (event: any) => {
    if (processModel) {
      let foundExistingFile = false;
      if (processModel.files.length > 0) {
        processModel.files.forEach((file) => {
          if (file.name === filesToUpload[0].name) {
            foundExistingFile = true;
          }
        });
      }
      if (foundExistingFile) {
        displayOverwriteConfirmation(filesToUpload[0].name);
        setFileUploadEvent(event);
      } else {
        doFileUpload(event);
      }
    }
    return null;
  };

  const handleFileUpload = (event: any) => {
    checkDuplicateFile(event);
    setShowFileUploadModal(false);
  };

  const fileUploadModal = () => {
    return (
      <Modal
        data-qa="modal-upload-file-dialog"
        open={showFileUploadModal}
        modalHeading="Upload File"
        primaryButtonText="Upload"
        primaryButtonDisabled={filesToUpload === null}
        secondaryButtonText="Cancel"
        onSecondarySubmit={handleFileUploadCancel}
        onRequestClose={handleFileUploadCancel}
        onRequestSubmit={handleFileUpload}
      >
        <FileUploader
          labelTitle="Upload files"
          labelDescription="Max file size is 500mb. Only .bpmn, .dmn, .json, and .md files are supported."
          buttonLabel="Add file"
          buttonKind="primary"
          size="md"
          filenameStatus="edit"
          role="button"
          accept={['.bpmn', '.dmn', '.json', '.md']}
          disabled={false}
          iconDescription="Delete file"
          name=""
          multiple={false}
          onDelete={() => setFilesToUpload(null)}
          onChange={(event: any) => setFilesToUpload(event.target.files)}
        />
      </Modal>
    );
  };

  const items = [
    'Upload File',
    'New BPMN File',
    'New DMN File',
    'New JSON File',
    'New Markdown File',
  ].map((item) => ({
    text: item,
  }));

  const addFileComponent = () => {
    return (
      <Dropdown
        id="inline"
        titleText=""
        size="lg"
        label="Add File"
        type="default"
        data-qa="process-model-add-file"
        onChange={(a: any) => {
          if (a.selectedItem.text === 'New BPMN File') {
            navigate(
              `/editor/process-models/${modifiedProcessModelId}/files?file_type=bpmn`,
            );
          } else if (a.selectedItem.text === 'Upload File') {
            setShowFileUploadModal(true);
          } else if (a.selectedItem.text === 'New DMN File') {
            navigate(
              `/editor/process-models/${modifiedProcessModelId}/files?file_type=dmn`,
            );
          } else if (a.selectedItem.text === 'New JSON File') {
            navigate(
              `/process-models/${modifiedProcessModelId}/form?file_ext=json`,
            );
          } else if (a.selectedItem.text === 'New Markdown File') {
            navigate(
              `/process-models/${modifiedProcessModelId}/form?file_ext=md`,
            );
          }
        }}
        items={items}
        itemToString={(item: any) => (item ? item.text : '')}
      />
    );
  };

  const readmeFileArea = () => {
    if (readmeFile) {
      return (
        <div className="readme-container">
          <Grid condensed fullWidth className="megacondensed">
            <Column md={7} lg={15} sm={3}>
              <p className="with-icons">{readmeFile.name}</p>
            </Column>
            <Column md={1} lg={1} sm={1}>
              <Can
                I="PUT"
                a={targetUris.processModelFileCreatePath}
                ability={ability}
              >
                <Button
                  kind="ghost"
                  data-qa="process-model-readme-file-edit"
                  renderIcon={Edit}
                  iconDescription="Edit README.md"
                  hasIconOnly
                  href={`/process-models/${modifiedProcessModelId}/form/${readmeFile.name}`}
                />
              </Can>
            </Column>
          </Grid>
          <hr />
          <MarkdownDisplayForFile
            apiPath={`/process-models/${modifiedProcessModelId}/files/${readmeFile.name}`}
          />
        </div>
      );
    }
    return (
      <>
        <p>No README file found</p>
        <Can
          I="POST"
          a={targetUris.processModelFileCreatePath}
          ability={ability}
        >
          <Button
            className="with-top-margin"
            data-qa="process-model-readme-file-create"
            href={`/process-models/${modifiedProcessModelId}/form?file_ext=md&default_file_name=README.md`}
            size="md"
          >
            Add README.md
          </Button>
        </Can>
      </>
    );
  };

  const updateSelectedTab = (newTabIndex: any) => {
    setSelectedTabIndex(newTabIndex.selectedIndex);
  };

  const tabArea = () => {
    if (!processModel) {
      return null;
    }

    let helpText = null;
    if (processModel.files.length === 0) {
      helpText = (
        <p className="no-results-message with-bottom-margin">
          <strong>
            **This process model does not have any files associated with it. Try
            creating a bpmn file by selecting &quot;New BPMN File&quot; in the
            dropdown below.**
          </strong>
        </p>
      );
    }

    return (
      <Tabs selectedIndex={selectedTabIndex} onChange={updateSelectedTab}>
        <TabList aria-label="List of tabs">
          <Tab>About</Tab>
          <Tab data-qa="process-model-files">Files</Tab>
          <Tab data-qa="process-instance-list-link">My process instances</Tab>
        </TabList>
        <TabPanels>
          <TabPanel>{readmeFileArea()}</TabPanel>
          <TabPanel>
            <Grid condensed fullWidth className="megacondensed">
              <Column md={6} lg={12} sm={4}>
                <Can
                  I="POST"
                  a={targetUris.processModelFileCreatePath}
                  ability={ability}
                >
                  {helpText}
                  <div className="with-bottom-margin">
                    Files
                    {processModel &&
                      processModel.bpmn_version_control_identifier &&
                      ` (revision ${processModel.bpmn_version_control_identifier})`}
                  </div>
                  {addFileComponent()}
                  <br />
                </Can>
                {processModelFileList()}
              </Column>
            </Grid>
          </TabPanel>
          <TabPanel>
            {selectedTabIndex !== 2 ? null : (
              <Can
                I="POST"
                a={targetUris.processInstanceListForMePath}
                ability={ability}
              >
                <ProcessInstanceListTable
                  additionalReportFilters={[
                    {
                      field_name: 'process_model_identifier',
                      field_value: processModel.id,
                    },
                  ]}
                  perPageOptions={[2, 5, 25]}
                  showLinkToReport
                  variant="for-me"
                />
              </Can>
            )}
          </TabPanel>
        </TabPanels>
      </Tabs>
    );
  };

  const processModelPublishMessage = () => {
    if (processModelPublished) {
      const prUrl: string = processModelPublished.pr_url;
      return (
        <Notification
          title="Model Published:"
          onClose={() => setProcessModelPublished(false)}
        >
          <a href={prUrl} target="_void()">
            View the changes and create a Pull Request
          </a>
        </Notification>
      );
    }
    return null;
  };

  if (processModel) {
    const processStartButton = (
      <Stack orientation="horizontal" gap={3}>
        <Can
          I="POST"
          a={targetUris.processInstanceCreatePath}
          ability={ability}
        >
          <>
            <ProcessInstanceRun processModel={processModel} />
            <br />
            <br />
          </>
        </Can>
      </Stack>
    );
    return (
      <>
        {fileUploadModal()}
        {confirmOverwriteFileDialog()}
        <ProcessBreadcrumb
          hotCrumbs={[
            ['Process Groups', '/process-groups'],
            {
              entityToExplode: processModel,
              entityType: 'process-model',
            },
          ]}
        />
        {processModelPublishMessage()}
        <Stack orientation="horizontal" gap={1}>
          <h1 className="with-icons">
            Process Model: {processModel.display_name}
          </h1>
          <Can I="PUT" a={targetUris.processModelShowPath} ability={ability}>
            <Button
              kind="ghost"
              data-qa="edit-process-model-button"
              renderIcon={Edit}
              iconDescription="Edit Process Model"
              hasIconOnly
              href={`/process-models/${modifiedProcessModelId}/edit`}
            />
          </Can>
          <Can I="DELETE" a={targetUris.processModelShowPath} ability={ability}>
            <ButtonWithConfirmation
              kind="ghost"
              data-qa="delete-process-model-button"
              renderIcon={TrashCan}
              iconDescription="Delete Process Model"
              hasIconOnly
              description={`Delete process model: ${processModel.display_name}`}
              onConfirmation={deleteProcessModel}
              confirmButtonLabel="Delete"
            />
          </Can>
          {!processModel.actions || processModel.actions.publish ? (
            <Can
              I="POST"
              a={targetUris.processModelPublishPath}
              ability={ability}
            >
              <Button
                kind="ghost"
                data-qa="publish-process-model-button"
                renderIcon={Upload}
                iconDescription="Publish Changes"
                hasIconOnly
                onClick={publishProcessModel}
                disabled={publishDisabled}
              />
            </Can>
          ) : null}
          <Can I="POST" a={targetUris.processModelTestsPath} ability={ability}>
            {hasTestCaseFiles ? (
              <ProcessModelTestRun titleText="Run all BPMN unit tests for this process model" />
            ) : null}
          </Can>
        </Stack>
        <p className="process-description">{processModel.description}</p>
        {processModel.primary_file_name && processModel.is_executable
          ? processStartButton
          : null}
        <div className="with-top-margin">{tabArea()}</div>
        {permissionsLoaded ? (
          <span data-qa="process-model-show-permissions-loaded" />
        ) : null}
      </>
    );
  }
  return null;
}
