import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Box, Tab, Tabs, MenuItem, Menu, Button } from '@mui/material';
import ArrowDropDownIcon from '@mui/icons-material/ArrowDropDown';
import Grid from '@mui/material/Grid';
import { Can, type AppAbility } from '../contexts/Can';
import { useNavigate } from 'react-router-dom';
import ProcessInstanceListTable from './ProcessInstanceListTable';
import ProcessModelFileList from './ProcessModelFileList';
import { ProcessFile } from '../interfaces';
import ProcessModelReadmeArea from './ProcessModelReadmeArea';

interface ProcessModelTabsProps {
  processModel: any;
  ability: AppAbility;
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
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
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
  const [addFileMenuAnchorEl, setAddFileMenuAnchorEl] =
    useState<null | HTMLElement>(null);

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

  const handleAddFileItemSelected = (selectedItem: string) => {
    setAddFileMenuAnchorEl(null);
    if (selectedItem === 'new_bpmn_file') {
      navigate(
        `/process-models/${modifiedProcessModelId}/files?file_type=bpmn`,
      );
    } else if (selectedItem === 'upload_file') {
      updateSelectedTab(1); // Switch to Files tab
      setShowFileUploadModal(true);
    } else if (selectedItem === 'new_dmn_file') {
      navigate(`/process-models/${modifiedProcessModelId}/files?file_type=dmn`);
    } else if (selectedItem === 'new_json_file') {
      navigate(`/process-models/${modifiedProcessModelId}/form?file_ext=json`);
    } else if (selectedItem === 'new_markdown_file') {
      navigate(`/process-models/${modifiedProcessModelId}/form?file_ext=md`);
    }
  };

  const addFileComponent = () => {
    // This is an action menu (each item performs a navigation/action immediately),
    // not a persisted value, so it is implemented as a button + menu rather than a
    // <select>. A <select> whose onChange navigates the page violates WCAG 3.2.2
    // (On Input): choosing an option activates it merely by changing focus/value,
    // with no separate, explicit activation step.
    return (
      <>
        <Button
          id="add-file-button"
          aria-controls={addFileMenuAnchorEl ? 'add-file-menu' : undefined}
          aria-haspopup="true"
          aria-expanded={addFileMenuAnchorEl ? 'true' : undefined}
          endIcon={<ArrowDropDownIcon />}
          onClick={(event) => setAddFileMenuAnchorEl(event.currentTarget)}
        >
          {t('add_file')}
        </Button>
        <Menu
          id="add-file-menu"
          anchorEl={addFileMenuAnchorEl}
          open={Boolean(addFileMenuAnchorEl)}
          onClose={() => setAddFileMenuAnchorEl(null)}
          MenuListProps={{ 'aria-labelledby': 'add-file-button' }}
        >
          {items.map((item) => (
            <MenuItem
              key={item}
              onClick={() => handleAddFileItemSelected(item)}
            >
              {t(item)}
            </MenuItem>
          ))}
        </Menu>
      </>
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
          <Grid size={{ xs: 12 }}>
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
              perPageOptions={[5, 25]}
              showLinkToReport
              variant="for-me"
            />
          </Can>
        </TabPanel>
      )}
    </>
  );
}
