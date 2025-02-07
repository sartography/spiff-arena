import React from 'react';
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
import ButtonWithConfirmation from './ButtonWithConfirmation';
import ProcessModelTestRun from './ProcessModelTestRun';
import { ProcessFile } from '../interfaces';

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

  const renderButtonElements = (
    processModelFile: ProcessFile,
    isPrimaryBpmnFile: boolean,
  ) => {
    const elements = [];

    let icon = <Visibility />;
    let actionWord = 'View';
    if (ability.can('PUT', targetUris.processModelFileCreatePath)) {
      icon = <Edit />;
      actionWord = 'Edit';
    }
    const editUrl = profileModelFileEditUrl(processModelFile);
    if (editUrl) {
      elements.push(
        <Can
          I="GET"
          a={targetUris.processModelFileCreatePath}
          ability={ability}
        >
          <IconButton
            aria-label={`${actionWord} File`}
            data-qa={`edit-file-${processModelFile.name.replace('.', '-')}`}
            href={editUrl}
          >
            {icon}
          </IconButton>
        </Can>,
      );
    }
    elements.push(
      <Can I="GET" a={targetUris.processModelFileCreatePath} ability={ability}>
        <IconButton
          aria-label="Download File"
          onClick={() =>
            window.open(
              `/${targetUris.processModelFilePath}/${processModelFile.name}`,
              '_blank',
            )
          }
        >
          <GetApp />
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
            renderIcon={<Delete />}
            hasIconOnly
            iconDescription="Delete File"
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
          <IconButton
            aria-label="Set As Primary File"
            onClick={() => onSetPrimaryFile(processModelFile.name)}
          >
            <Favorite />
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
            <span className="primary-file-text-suffix">Primary File</span>
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
            <TableCell>Name</TableCell>
            <TableCell align="right">Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>{tags}</TableBody>
      </Table>
    </TableContainer>
  );
}
