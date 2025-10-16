import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Upload, Edit, Delete, ContentCopy, MoreVert } from '@mui/icons-material';
import { Stack, IconButton, Typography, Menu, MenuItem, ListItemIcon, ListItemText } from '@mui/material';
import { Can } from '@casl/react';
// Example icon
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
import ProcessModelTabs from '../components/ProcessModelTabs';
import ProcessModelFileUploadModal from '../components/ProcessModelFileUploadModal';
import ProcessModelCopyModal from '../components/ProcessModelCopyModal';
import SpiffTooltip from '../components/SpiffTooltip';

export default function ProcessModelShow() {
  const params = useParams();
  const { addError, removeError } = useAPIError();
  const navigate = useNavigate();
  const { t } = useTranslation();

  const [processModel, setProcessModel] = useState<ProcessModel | null>(null);
  const [reloadModel, setReloadModel] = useState<boolean>(false);
  const [showFileUploadModal, setShowFileUploadModal] =
    useState<boolean>(false);
  const [showCopyModal, setShowCopyModal] = useState<boolean>(false);
  const [processModelPublished, setProcessModelPublished] = useState<any>(null);
  const [publishDisabled, setPublishDisabled] = useState<boolean>(false);
  const [selectedTabIndex, setSelectedTabIndex] = useState<number>(1);
  const [readmeFile, setReadmeFile] = useState<ProcessFile | null>(null);
  const [actionsMenuAnchor, setActionsMenuAnchor] = useState<null | HTMLElement>(null);

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
    return !!processModelFile.name.match(/^test_.*\.json$/);
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
      let foundReadme = null;
      result.files.forEach((file: ProcessFile) => {
        if (file.name === 'README.md') {
          foundReadme = file;
          newTabIndex = 0;
        }
      });
      setReadmeFile(foundReadme);
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

  const doFileUpload = (filesToUpload: File[], forceOverwrite = false) => {
    if (!filesToUpload || filesToUpload.length === 0) {
      return; // No files to upload
    }
    removeError();
    const url = `/process-models/${modifiedProcessModelId}/files`;
    const formData = new FormData();
    formData.append('file', filesToUpload[0]);
    formData.append('fileName', filesToUpload[0].name);
    formData.append('overwrite', forceOverwrite.toString()); // Add overwrite parameter

    HttpService.makeCallToBackend({
      path: url,
      successCallback: onUploadedCallback,
      httpMethod: 'POST',
      postBody: formData,
      failureCallback: addError,
    });
  };

  const handleFileUploadCancel = () => {
    setShowFileUploadModal(false);
  };

  const checkDuplicateFile = (files: File[], forceOverwrite = false) => {
    if (forceOverwrite) {
      doFileUpload(files, true);
    } else {
      doFileUpload(files);
    }
    setShowFileUploadModal(false);
  };

  const handleCopyCancel = () => {
    setShowCopyModal(false);
  };

  const handleActionsMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setActionsMenuAnchor(event.currentTarget);
  };

  const handleActionsMenuClose = () => {
    setActionsMenuAnchor(null);
  };

  const handleCopyConfirm = (newId: string, newDisplayName?: string) => {
    removeError();
    const url = `/process-models/${modifiedProcessModelId}/copy`;
    const postBody: { id: string; display_name?: string } = {
      id: newId,
    };

    // Only include display_name in request if it was provided
    if (newDisplayName && newDisplayName.trim()) {
      postBody.display_name = newDisplayName.trim();
    }

    HttpService.makeCallToBackend({
      path: url,
      httpMethod: 'POST',
      postBody,
      successCallback: (result: ProcessModel) => {
        setShowCopyModal(false);
        // Navigate to the new process model, replacing forward slashes with colons
        const navigationId = result.id.replace(/\//g, ':');
        navigate(`/process-models/${navigationId}`);
      },
      failureCallback: addError,
    });
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
            {t('view_changes_create_pr')}
          </a>
        </Notification>
      );
    }
    return null;
  };

  if (processModel) {
    const processStartButton = (
      <Can I="POST" a={targetUris.processInstanceCreatePath} ability={ability}>
        <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
          <ProcessInstanceRun processModel={processModel} />
        </Stack>
      </Can>
    );
    return (
      <>
        <ProcessModelFileUploadModal
          showFileUploadModal={showFileUploadModal}
          processModel={processModel}
          doFileUpload={doFileUpload}
          handleFileUploadCancel={handleFileUploadCancel}
          checkDuplicateFile={checkDuplicateFile}
          setShowFileUploadModal={setShowFileUploadModal}
        />
        <ProcessModelCopyModal
          showCopyModal={showCopyModal}
          processModel={processModel}
          handleCopyCancel={handleCopyCancel}
          handleCopyConfirm={handleCopyConfirm}
        />
        <ProcessBreadcrumb
          hotCrumbs={[
            [t('process_groups'), '/process-groups'],
            {
              entityToExplode: processModel,
              entityType: 'process-model',
            },
          ]}
        />
        {processModelPublishMessage()}
        <Stack direction="row" spacing={1} alignItems="center">
          <Typography variant="h2" component="h1">
            {t('process_model')}: {processModel.display_name}
          </Typography>

          {/* More Actions Menu */}
          <SpiffTooltip title={t('more_actions')} placement="top">
            <IconButton
              data-testid="more-actions-button"
              onClick={handleActionsMenuOpen}
            >
              <MoreVert />
            </IconButton>
          </SpiffTooltip>
          <Menu
            anchorEl={actionsMenuAnchor}
            open={Boolean(actionsMenuAnchor)}
            onClose={handleActionsMenuClose}
            anchorOrigin={{
              vertical: 'bottom',
              horizontal: 'right',
            }}
            transformOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
          >
            <Can I="PUT" a={targetUris.processModelShowPath} ability={ability}>
              <MenuItem
                component="a"
                href={`/process-models/${modifiedProcessModelId}/edit`}
                data-testid="edit-process-model-menu-item"
                onClick={handleActionsMenuClose}
              >
                <ListItemIcon>
                  <Edit fontSize="small" />
                </ListItemIcon>
                <ListItemText>{t('edit_process_model')}</ListItemText>
              </MenuItem>
            </Can>
            <MenuItem
              data-testid="copy-process-model-menu-item"
              onClick={() => {
                setShowCopyModal(true);
                handleActionsMenuClose();
              }}
            >
              <ListItemIcon>
                <ContentCopy fontSize="small" />
              </ListItemIcon>
              <ListItemText>{t('copy_process_model')}</ListItemText>
            </MenuItem>
            <Can I="DELETE" a={targetUris.processModelShowPath} ability={ability}>
              <MenuItem
                data-testid="delete-process-model-menu-item"
                onClick={() => {
                  handleActionsMenuClose();
                  // The ButtonWithConfirmation will handle the confirmation dialog
                  if (window.confirm(t('delete_process_model_confirm', {
                    processModelName: processModel.display_name,
                  }))) {
                    deleteProcessModel();
                  }
                }}
              >
                <ListItemIcon>
                  <Delete fontSize="small" />
                </ListItemIcon>
                <ListItemText>{t('delete_process_model')}</ListItemText>
              </MenuItem>
            </Can>
          </Menu>

          {/* Keep frequently used actions outside menu */}
          {!processModel.actions || processModel.actions.publish ? (
            <Can
              I="POST"
              a={targetUris.processModelPublishPath}
              ability={ability}
            >
              <SpiffTooltip title={t('publish_process_model')} placement="top">
                <IconButton
                  color="primary"
                  data-testid="publish-process-model-button"
                  onClick={publishProcessModel}
                  disabled={publishDisabled}
                >
                  <Upload />
                </IconButton>
              </SpiffTooltip>
            </Can>
          ) : null}
          <Can I="POST" a={targetUris.processModelTestsPath} ability={ability}>
            {hasTestCaseFiles ? (
              <ProcessModelTestRun titleText={t('run_bpmn_tests')} />
            ) : null}
          </Can>
        </Stack>
        <Typography variant="body1" className="process-description">
          {processModel.description}
        </Typography>
        {processModel.primary_file_name && processModel.is_executable
          ? processStartButton
          : null}

        <br />
        <br />

        <ProcessModelTabs
          processModel={processModel}
          ability={ability}
          targetUris={targetUris}
          modifiedProcessModelId={modifiedProcessModelId}
          selectedTabIndex={selectedTabIndex}
          updateSelectedTab={setSelectedTabIndex}
          onDeleteFile={onDeleteFile}
          onSetPrimaryFile={onSetPrimaryFile}
          isTestCaseFile={isTestCaseFile}
          readmeFile={readmeFile}
          setShowFileUploadModal={setShowFileUploadModal}
        />
        {permissionsLoaded ? (
          <span data-testid="process-model-show-permissions-loaded" />
        ) : null}
      </>
    );
  }
  return null;
}
