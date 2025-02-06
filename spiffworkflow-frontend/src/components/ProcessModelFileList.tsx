import React from 'react';
import { Link } from 'react-router-dom';
import { Download, Edit, Favorite, TrashCan, View } from '@carbon/icons-react';
import {
  Button,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@carbon/react';
import { Can } from '@casl/react';
import { PureAbility } from '@casl/ability';
import ButtonWithConfirmation from './ButtonWithConfirmation';
import ProcessModelTestRun from './ProcessModelTestRun';
import { ProcessFile } from '../interfaces';
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
  const { addError, removeError } = useAPIError();
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

  const renderButtonElements = (
    processModelFile: ProcessFile,
    isPrimaryBpmnFile: boolean,
  ) => {
    const elements = [];

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
          href={profileModelFileEditUrl(processModelFile)}
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
