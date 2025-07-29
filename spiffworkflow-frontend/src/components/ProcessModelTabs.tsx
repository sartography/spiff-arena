import React from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Grid,
  Tab,
  Tabs,
  MenuItem,
  Select,
  Typography,
  FormControl,
  InputLabel,
} from '@mui/material';
import { Can } from '@casl/react'; // Corrected import
import { useNavigate } from 'react-router-dom';
import { PureAbility } from '@casl/ability';
import ProcessInstanceListTable from './ProcessInstanceListTable';
import ProcessModelFileList from './ProcessModelFileList';
import { ProcessFile } from '../interfaces';
import ProcessModelReadmeArea from './ProcessModelReadmeArea';

interface ProcessModelTabsProps {
  processModel: any;
  ability: PureAbility;
  targetUris: any;
  modifiedProcessModelId: string;
  selectedTabIndex: number;
  updateSelectedTab: (newTabIndex: any) => void;
  onDeleteFile: (fileName: string) => void;
  onSetPrimaryFile: (fileName: string) => void;
  isTestCaseFile: (processModelFile: ProcessFile) => boolean;
  readmeFile: ProcessFile | null;
  setShowFileUploadModal: Function;
}

interface ProcessModelTabPanelProps {
  children?: any;
  value: number;
  index: number;
}

function TabPanel({ children, value, index }: ProcessModelTabPanelProps) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          <Typography>{children}</Typography>
        </Box>
      )}
    </div>
  );
}

export default function ProcessModelTabs({
  processModel,
  ability,
  targetUris,
  modifiedProcessModelId,
  selectedTabIndex,
  updateSelectedTab,
  onDeleteFile,
  onSetPrimaryFile,
  isTestCaseFile,
  readmeFile,
  setShowFileUploadModal,
}: ProcessModelTabsProps) {
  const navigate = useNavigate();
  const { t } = useTranslation();

  if (!processModel) {
    return null;
  }

  let helpText = null;
  if (processModel.files.length === 0) {
    helpText = (
      <p className="no-results-message with-bottom-margin">
        <strong>{t('process_model_no_files_help')}</strong>
      </p>
    );
  }

  const items = [
    'upload_file',
    'new_bpmn_file',
    'new_dmn_file',
    'new_json_file',
    'new_markdown_file',
  ];

  const addFileComponent = () => {
    return (
      <FormControl fullWidth>
        <InputLabel id="add-file-select-label">{t('add_file')}</InputLabel>
        <Select
          labelId="add-file-select-label"
          label={t('add_file')}
          onChange={(event) => {
            const selectedItem = event.target.value;
            if (selectedItem === 'new_bpmn_file') {
              navigate(
                `/process-models/${modifiedProcessModelId}/files?file_type=bpmn`,
              );
            } else if (selectedItem === 'upload_file') {
              updateSelectedTab(1); // Switch to Files tab
              setShowFileUploadModal(true);
            } else if (selectedItem === 'new_dmn_file') {
              navigate(
                `/process-models/${modifiedProcessModelId}/files?file_type=dmn`,
              );
            } else if (selectedItem === 'new_json_file') {
              navigate(
                `/process-models/${modifiedProcessModelId}/form?file_ext=json`,
              );
            } else if (selectedItem === 'new_markdown_file') {
              navigate(
                `/process-models/${modifiedProcessModelId}/form?file_ext=md`,
              );
            }
          }}
          value=""
        >
          {items.map((item) => (
            <MenuItem key={item} value={item}>
              {t(item)}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    );
  };

  return (
    <>
      <Tabs
        value={selectedTabIndex}
        onChange={(_event, newValue) => {
          updateSelectedTab(newValue);
        }}
        aria-label="List of tabs"
      >
        <Tab value={0} label={t('about')} />
        <Tab value={1} label={t('files')} data-testid="process-model-files" />
        <Tab
          value={2}
          label={t('my_process_instances')}
          data-testid="process-instance-list-link"
        />
      </Tabs>
      <TabPanel value={selectedTabIndex} index={0}>
        <ProcessModelReadmeArea
          readmeFile={readmeFile}
          ability={ability}
          targetUris={targetUris}
          modifiedProcessModelId={modifiedProcessModelId}
        />
      </TabPanel>
      <TabPanel value={selectedTabIndex} index={1}>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <Can
              I="POST"
              a={targetUris.processModelFileCreatePath}
              ability={ability}
            >
              {helpText}
              <div className="with-bottom-margin">
                {processModel && processModel.bpmn_version_control_identifier
                  ? t('files_with_revision', {
                      revision: processModel.bpmn_version_control_identifier,
                    })
                  : t('files')}
              </div>
              {addFileComponent()}
              <br />
            </Can>
            <ProcessModelFileList
              processModel={processModel}
              ability={ability}
              targetUris={targetUris}
              modifiedProcessModelId={modifiedProcessModelId}
              onDeleteFile={onDeleteFile}
              onSetPrimaryFile={onSetPrimaryFile}
              isTestCaseFile={isTestCaseFile}
            />
          </Grid>
        </Grid>
      </TabPanel>
      {selectedTabIndex === 2 && (
        <TabPanel value={selectedTabIndex} index={2}>
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
        </TabPanel>
      )}
    </>
  );
}
