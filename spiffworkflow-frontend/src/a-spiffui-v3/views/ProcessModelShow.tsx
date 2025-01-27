import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import {
  Download as DownloadIcon,
  Edit as EditIcon,
  Favorite as FavoriteIcon,
  Delete as DeleteIcon,
  Upload as UploadIcon,
  Visibility as VisibilityIcon,
} from '@mui/icons-material';
import {
  Button,
  Grid,
  Modal,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Tabs,
  Tab,
  Box,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  IconButton,
  Typography,
} from '@mui/material';
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
// import ProcessInstanceListTable from '../components/ProcessInstanceListTable';

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
    let icon = VisibilityIcon;
    let actionWord = 'View';
    if (ability.can('PUT', targetUris.processModelFileCreatePath)) {
      icon = EditIcon;
      actionWord = 'Edit';
    }
    elements.push(
      <Can I="GET" a={targetUris.processModelFileCreatePath} ability={ability}>
        <IconButton
          aria-label={`${actionWord} File`}
          size="large"
          data-qa={`edit-file-${processModelFile.name.replace('.', '-')}`}
          onClick={() => navigateToFileEdit(processModelFile)}
        >
          <icon />
        </IconButton>
      </Can>,
    );
    elements.push(
      <Can I="GET" a={targetUris.processModelFileCreatePath} ability={ability}>
        <IconButton
          aria-label="Download File"
          size="large"
          onClick={() => downloadFile(processModelFile.name)}
        >
          <DownloadIcon />
        </IconButton>
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
            aria-label="Delete File"
            description={`Delete file: ${processModelFile.name}`}
            onConfirmation={() => {
              onDeleteFile(processModelFile.name);
            }}
            confirmButtonLabel="Delete"
            classNameForModal="modal-within-table-cell"
            icon={<DeleteIcon />}
          />
        </Can>,
      );
    }
    if (processModelFile.name.match(/\.bpmn$/) && !isPrimaryBpmnFile) {
      elements.push(
        <Can I="PUT" a={targetUris.processModelShowPath} ability={ability}>
          <IconButton
            aria-label="Set As Primary File"
            size="large"
            onClick={() => onSetPrimaryFile(processModelFile.name)}
          >
            <FavoriteIcon />
          </IconButton>
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
        <Table size="medium" aria-label="Process Model Files">
          <TableHead>
            <TableRow>
              <TableCell key="Name">Name</TableCell>
              <TableCell key="Actions" align="right">
                Actions
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>{tags}</TableBody>
        </Table>
      );
    }
    return null;
  };

  const [fileUploadEvent, setFileUploadEvent] = useState(null);
  const [duplicateFilename, setDuplicateFilename] = useState<string>('');
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
  const displayOverwriteConfirmation = (filename: string) => {
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
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Typography variant="body1">Upload files</Typography>
          <Typography variant="body2" color="textSecondary">
            Max file size is 500mb. Only .bpmn, .dmn, .json, and .md files are
            supported.
          </Typography>
          <input
            type="file"
            accept=".bpmn,.dmn,.json,.md"
            style={{ display: 'none' }}
            id="file-upload-input"
            onChange={(event: any) => setFilesToUpload(event.target.files)}
          />
          <label htmlFor="file-upload-input">
            <Button variant="contained" component="span">
              Add file
            </Button>
          </label>
          {filesToUpload && (
            <Typography variant="body2">
              Selected file: {filesToUpload[0].name}
            </Typography>
          )}
          <Button
            variant="outlined"
            onClick={() => setFilesToUpload(null)}
            disabled={!filesToUpload}
          >
            Clear file
          </Button>
        </Box>
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
      <FormControl sx={{ m: 1, minWidth: 120 }} size="small">
        <InputLabel id="add-file-dropdown-label">Add File</InputLabel>
        <Select
          labelId="add-file-dropdown-label"
          id="add-file-dropdown"
          label="Add File"
          data-qa="process-model-add-file"
          onChange={(event: any) => {
            const selectedValue = event.target.value;
            if (selectedValue === 'New BPMN File') {
              navigate(
                `/editor/process-models/${modifiedProcessModelId}/files?file_type=bpmn`,
              );
            } else if (selectedValue === 'Upload File') {
              setShowFileUploadModal(true);
            } else if (selectedValue === 'New DMN File') {
              navigate(
                `/editor/process-models/${modifiedProcessModelId}/files?file_type=dmn`,
              );
            } else if (selectedValue === 'New JSON File') {
              navigate(
                `/process-models/${modifiedProcessModelId}/form?file_ext=json`,
              );
            } else if (selectedValue === 'New Markdown File') {
              navigate(
                `/process-models/${modifiedProcessModelId}/form?file_ext=md`,
              );
            }
          }}
        >
          {items.map((item) => (
            <MenuItem key={item.text} value={item.text}>
              {item.text}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    );
  };

  const readmeFileArea = () => {
    if (readmeFile) {
      return (
        <div className="readme-container">
          <Grid condensed fullWidth className="megacondensed">
            <Grid container alignItems="center">
              <Grid item xs>
                <Typography variant="h6" className="with-icons">
                  {readmeFile.name}
                </Typography>
              </Grid>
              <Grid item>
                <Can
                  I="PUT"
                  a={targetUris.processModelFileCreatePath}
                  ability={ability}
                >
                  <IconButton
                    data-qa="process-model-readme-file-edit"
                    aria-label="Edit README.md"
                    href={`/process-models/${modifiedProcessModelId}/form/${readmeFile.name}`}
                  >
                    <EditIcon />
                  </IconButton>
                </Can>
              </Grid>
            </Grid>
            <hr />
            <MarkdownDisplayForFile
              apiPath={`/process-models/${modifiedProcessModelId}/files/${readmeFile.name}`}
            />
          </Grid>
        </div>
      );
    }
    return (
      <Box>
        <Typography>No README file found</Typography>
        <Can
          I="POST"
          a={targetUris.processModelFileCreatePath}
          ability={ability}
        >
          <Button
            className="with-top-margin"
            data-qa="process-model-readme-file-create"
            href={`/process-models/${modifiedProcessModelId}/form?file_ext=md&default_file_name=README.md`}
            size="medium"
            variant="contained"
          >
            Add README.md
          </Button>
        </Can>
      </Box>
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
      <Box sx={{ width: '100%' }}>
        <Tabs
          value={selectedTabIndex}
          onChange={updateSelectedTab}
          aria-label="Process Model Tabs"
        >
          <Tab label="About" />
          <Tab label="Files" data-qa="process-model-files" />
          <Tab
            label="My process instances"
            data-qa="process-instance-list-link"
          />
        </Tabs>
        <Box sx={{ padding: 2 }}>
          {selectedTabIndex === 0 && readmeFileArea()}
          {selectedTabIndex === 1 && (
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <Can
                  I="POST"
                  a={targetUris.processModelFileCreatePath}
                  ability={ability}
                >
                  {helpText}
                  <Box className="with-bottom-margin">
                    <Typography variant="h6">
                      Files
                      {processModel &&
                        processModel.bpmn_version_control_identifier &&
                        ` (revision ${processModel.bpmn_version_control_identifier})`}
                    </Typography>
                  </Box>
                  {addFileComponent()}
                  <br />
                </Can>
                {processModelFileList()}
              </Grid>
            </Grid>
          )}
          {selectedTabIndex === 2 && (
            <Can
              I="POST"
              a={targetUris.processInstanceListForMePath}
              ability={ability}
            >
              {/* <ProcessInstanceListTable */}
              {/*   additionalReportFilters={[ */}
              {/*     { */}
              {/*       field_name: 'process_model_identifier', */}
              {/*       field_value: processModel.id, */}
              {/*     }, */}
              {/*   ]} */}
              {/*   perPageOptions={[2, 5, 25]} */}
              {/*   showLinkToReport */}
              {/*   variant="for-me" */}
              {/* /> */}
            </Can>
          )}
        </Box>
      </Box>
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
        <Stack direction="row" alignItems="center" spacing={1}>
          <Typography variant="h4" className="with-icons">
            Process Model: {processModel.display_name}
          </Typography>
          <Can I="PUT" a={targetUris.processModelShowPath} ability={ability}>
            <IconButton
              data-qa="edit-process-model-button"
              aria-label="Edit Process Model"
              href={`/process-models/${modifiedProcessModelId}/edit`}
            >
              <EditIcon />
            </IconButton>
          </Can>
          <Can I="DELETE" a={targetUris.processModelShowPath} ability={ability}>
            <ButtonWithConfirmation
              data-qa="delete-process-model-button"
              aria-label="Delete Process Model"
              description={`Delete process model: ${processModel.display_name}`}
              onConfirmation={deleteProcessModel}
              confirmButtonLabel="Delete"
              icon={<DeleteIcon />}
            />
          </Can>
          {!processModel.actions || processModel.actions.publish ? (
            <Can
              I="POST"
              a={targetUris.processModelPublishPath}
              ability={ability}
            >
              <IconButton
                data-qa="publish-process-model-button"
                aria-label="Publish Changes"
                onClick={publishProcessModel}
                disabled={publishDisabled}
              >
                <UploadIcon />
              </IconButton>
            </Can>
          ) : null}
          <Can I="POST" a={targetUris.processModelTestsPath} ability={ability}>
            {hasTestCaseFiles ? (
              <ProcessModelTestRun titleText="Run all BPMN unit tests for this process model" />
            ) : null}
          </Can>
        </Stack>
        <Typography variant="body1" className="process-description">
          {processModel.description}
        </Typography>
        {processModel.primary_file_name && processModel.is_executable
          ? processStartButton
          : null}
        <Box className="with-top-margin">{tabArea()}</Box>
        {permissionsLoaded ? (
          <span data-qa="process-model-show-permissions-loaded" />
        ) : null}
      </>
    );
  }
  return null;
}
