import React from 'react';
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

  const items = [
    'Upload File',
    'New BPMN File',
    'New DMN File',
    'New JSON File',
    'New Markdown File',
  ];

  const addFileComponent = () => {
    return (
      <FormControl fullWidth>
        <InputLabel id="add-file-select-label">Add File</InputLabel>
        <Select
          labelId="add-file-select-label"
          label="Add File"
          onChange={(event) => {
            const selectedItem = event.target.value;
            if (selectedItem === 'New BPMN File') {
              navigate(
                `/process-models/${modifiedProcessModelId}/files?file_type=bpmn`,
              );
            } else if (selectedItem === 'Upload File') {
              // Handled by parent component via prop
              updateSelectedTab(1); // Switch to Files tab
              // Open file upload modal (handled by parent)
              setShowFileUploadModal(true);
            } else if (selectedItem === 'New DMN File') {
              navigate(
                `/process-models/${modifiedProcessModelId}/files?file_type=dmn`,
              );
            } else if (selectedItem === 'New JSON File') {
              navigate(
                `/process-models/${modifiedProcessModelId}/form?file_ext=json`,
              );
            } else if (selectedItem === 'New Markdown File') {
              navigate(
                `/process-models/${modifiedProcessModelId}/form?file_ext=md`,
              );
            }
          }}
          value=""
        >
          {items.map((item) => (
            <MenuItem key={item} value={item}>
              {item}
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
        onChange={(event, newValue) => {
          updateSelectedTab(newValue);
        }}
        aria-label="List of tabs"
      >
        <Tab value={0} label="About" />
        <Tab value={1} label="Files" data-qa="process-model-files" />
        <Tab
          value={2}
          label="My process instances"
          data-qa="process-instance-list-link"
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
                Files
                {processModel &&
                  processModel.bpmn_version_control_identifier &&
                  ` (revision ${processModel.bpmn_version_control_identifier})`}
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
