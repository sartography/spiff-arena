import React from 'react';
import { Button, Column, Grid } from '@carbon/react';
import { Can } from '@casl/react';
import { Edit } from '@carbon/icons-react';
import { PureAbility } from '@casl/ability';
import MarkdownDisplayForFile from './MarkdownDisplayForFile';
import { ProcessFile } from '../interfaces';

interface ProcessModelReadmeAreaProps {
  readmeFile: ProcessFile | null;
  ability: PureAbility;
  targetUris: any;
  modifiedProcessModelId: string;
}

export default function ProcessModelReadmeArea({
  readmeFile,
  ability,
  targetUris,
  modifiedProcessModelId,
}: ProcessModelReadmeAreaProps) {
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
      <Can I="POST" a={targetUris.processModelFileCreatePath} ability={ability}>
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
}
