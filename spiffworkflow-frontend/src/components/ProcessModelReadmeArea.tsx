import React from 'react';
import { useTranslation } from 'react-i18next';
import { Button, IconButton } from '@mui/material';
import Grid from '@mui/material/Grid';
import { Can } from '@casl/react';
import EditIcon from '@mui/icons-material/Edit';
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
  const { t } = useTranslation();
  if (readmeFile) {
    return (
      <div className="readme-container">
        <Grid container spacing={1} alignItems="center">
          <Grid size={{ xs: 9, md: 11 }}>
            <p className="with-icons">{readmeFile.name}</p>
          </Grid>
          <Grid size={{ xs: 3, md: 1 }} textAlign="right">
            <Can
              I="PUT"
              a={targetUris.processModelFileCreatePath}
              ability={ability}
            >
              <IconButton
                data-testid="process-model-readme-file-edit"
                aria-label={t('edit_readme')}
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
      </div>
    );
  }
  return (
    <>
      <p>{t('no_readme_file')}</p>
      <Can I="POST" a={targetUris.processModelFileCreatePath} ability={ability}>
        <Button
          className="with-top-margin"
          data-testid="process-model-readme-file-create"
          href={`/process-models/${modifiedProcessModelId}/form?file_ext=md&default_file_name=README.md`}
          variant="contained"
        >
          {t('add_readme')}
        </Button>
      </Can>
    </>
  );
}
