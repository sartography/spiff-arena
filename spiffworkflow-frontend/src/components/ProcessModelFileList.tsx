import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import {
  Edit,
  GetApp,
  Delete,
  Favorite,
  Visibility,
} from '@mui/icons-material';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TableContainer,
  IconButton,
} from '@mui/material';
import { Can } from '@casl/react';
import { PureAbility } from '@casl/ability';
import ConfirmIconButton from './ConfirmIconButton';
import ProcessModelTestRun from './ProcessModelTestRun';
import { ProcessFile } from '../interfaces';
import SpiffTooltip from './SpiffTooltip';
import HttpService from '../services/HttpService';
import useAPIError from '../hooks/UseApiError';

interface ProcessModelFileListProps {
  processModel: any;
  ability: PureAbility;
  targetUris: any;
  modifiedProcessModelId: string;
  onDeleteFile: (fileName: string) => void;
  onSetPrimaryFile: (fileName: string) => void;
  isTestCaseFile: (processModelFile: ProcessFile) => boolean;
}

export default function ProcessModelFileList({
  processModel,
  ability,
  targetUris,
  modifiedProcessModelId,
  onDeleteFile,
  onSetPrimaryFile,
  isTestCaseFile,
}: ProcessModelFileListProps) {
  const { t } = useTranslation();
  const { addError, removeError } = useAPIError();
  const profileModelFileEditUrl = (processModelFile: ProcessFile) => {
    if (processModel) {
      if (processModelFile.name.match(/\.(dmn|bpmn)$/)) {
        return `/process-models/${modifiedProcessModelId}/files/${processModelFile.name}`;
      }
      if (processModelFile.name.match(/\.(json|md)$/)) {
        return `/process-models/${modifiedProcessModelId}/form/${processModelFile.name}`;
      }
    }
    return null;
  };

  const handleProcessModelFileResult = (processModelFile: ProcessFile) => {
    if (
      !('file_contents' in processModelFile) ||
      processModelFile.file_contents === undefined
    ) {
      addError({
        message: t('file_contents_not_found', { file: processModelFile.name }),
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

  const renderButtonElements = (
    processModelFile: ProcessFile,
    isPrimaryBpmnFile: boolean,
  ) => {
    const elements = [];

    let icon = <Visibility />;
    let actionWord = t('view');
    if (ability.can('PUT', targetUris.processModelFileCreatePath)) {
      icon = <Edit />;
      actionWord = t('edit');
    }
    const editUrl = profileModelFileEditUrl(processModelFile);
    if (editUrl) {
      elements.push(
        <Can
          I="GET"
          a={targetUris.processModelFileCreatePath}
          ability={ability}
        >
          <SpiffTooltip title={`${actionWord} ${t('file')}`} placement="top">
            <IconButton
              aria-label={`${actionWord} ${t('file')}`}
              data-testid={`edit-file-${processModelFile.name.replace('.', '-')}`}
              href={editUrl}
            >
              {icon}
            </IconButton>
          </SpiffTooltip>
        </Can>,
      );
    }
    elements.push(
      <Can I="GET" a={targetUris.processModelFileCreatePath} ability={ability}>
        <SpiffTooltip title={t('download_file')} placement="top">
          <IconButton
            aria-label={t('download_file')}
            onClick={() => downloadFile(processModelFile.name)}
          >
            <GetApp />
          </IconButton>
        </SpiffTooltip>
      </Can>,
    );

    if (!isPrimaryBpmnFile) {
      elements.push(
        <Can
          I="DELETE"
          a={targetUris.processModelFileCreatePath}
          ability={ability}
        >
          <ConfirmIconButton
            renderIcon={<Delete />}
            iconDescription={t('delete_file')}
            description={t('delete_file_description', {
              file: processModelFile.name,
            })}
            onConfirmation={() => {
              onDeleteFile(processModelFile.name);
            }}
            confirmButtonLabel={t('delete')}
          />
        </Can>,
      );
    }
    if (processModelFile.name.match(/\.bpmn$/) && !isPrimaryBpmnFile) {
      elements.push(
        <Can I="PUT" a={targetUris.processModelShowPath} ability={ability}>
          <SpiffTooltip title={t('set_as_primary_file')} placement="top">
            <IconButton
              aria-label={t('set_as_primary_file')}
              onClick={() => onSetPrimaryFile(processModelFile.name)}
            >
              <Favorite />
            </IconButton>
          </SpiffTooltip>
        </Can>,
      );
    }
    if (isTestCaseFile(processModelFile)) {
      elements.push(
        <Can I="POST" a={targetUris.processModelTestsPath} ability={ability}>
          <ProcessModelTestRun
            processModelFile={processModelFile}
            titleText={t('run_bpmn_unit_tests')}
            classNameForModal="modal-within-table-cell"
          />
        </Can>,
      );
    }
    return elements;
  };

  if (!processModel) {
    return null;
  }

  const tags = processModel.files
    .map((processModelFile: ProcessFile) => {
      if (!processModelFile.name.match(/\.(dmn|bpmn|json|md)$/)) {
        return undefined;
      }
      const isPrimaryBpmnFile =
        processModelFile.name === processModel.primary_file_name;

      const actionsTableCell = (
        <TableCell key={`${processModelFile.name}-action`} align="right">
          {renderButtonElements(processModelFile, isPrimaryBpmnFile)}
        </TableCell>
      );

      let primarySuffix = null;
      if (isPrimaryBpmnFile) {
        primarySuffix = (
          <span>
            &nbsp;-{' '}
            <span className="primary-file-text-suffix">
              {t('primary_file')}
            </span>
          </span>
        );
      }
      let fileLink = null;
      const fileUrl = profileModelFileEditUrl(processModelFile);
      if (fileUrl) {
        fileLink = <Link to={fileUrl}>{processModelFile.name}</Link>;
      }
      return (
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
    })
    .filter((element: any) => element !== undefined);

  if (tags.length === 0) {
    return null;
  }

  return (
    <TableContainer>
      <Table size="medium" className="process-model-file-table">
        <TableHead>
          <TableRow>
            <TableCell>{t('name')}</TableCell>
            <TableCell align="right">{t('actions')}</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>{tags}</TableBody>
      </Table>
    </TableContainer>
  );
}
