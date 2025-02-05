import {
  Column,
  Dropdown,
  Grid,
  Tab,
  TabList,
  TabPanel,
  TabPanels,
  Tabs,
} from '@carbon/react';
import { Can } from '@casl/ability';
import { useNavigate } from 'react-router-dom';
import ProcessInstanceListTable from './ProcessInstanceListTable';
import ProcessModelFileList from './ProcessModelFileList';
import { Ability } from '@casl/ability';
import { ProcessFile } from '../interfaces';

interface ProcessModelTabsProps {
  processModel: any;
  ability: Ability;
  targetUris: any;
  modifiedProcessModelId: string;
  selectedTabIndex: number;
  updateSelectedTab: (newTabIndex: any) => void;
  onDeleteFile: (fileName: string) => void;
  onSetPrimaryFile: (fileName: string) => void;
  isTestCaseFile: (processModelFile: ProcessFile) => boolean;
}

const ProcessModelTabs: React.FC<ProcessModelTabsProps> = ({
  processModel,
  ability,
  targetUris,
  modifiedProcessModelId,
  selectedTabIndex,
  updateSelectedTab,
  onDeleteFile,
  onSetPrimaryFile,
  isTestCaseFile
}) => {
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
  ].map((item) => ({
    text: item,
  }));

  const addFileComponent = () => {
    return (
      <Dropdown
        id="inline"
        titleText=""
        size="lg"
        label="Add File"
        type="default"
        data-qa="process-model-add-file"
        onChange={(a: any) => {
          if (a.selectedItem.text === 'New BPMN File') {
            navigate(
              `/editor/process-models/${modifiedProcessModelId}/files?file_type=bpmn`,
            );
          } else if (a.selectedItem.text === 'Upload File') {
            // Handled by parent component via prop
            updateSelectedTab({ selectedIndex: 1 }); // Switch to Files tab
            // Open file upload modal (handled by parent)
            // setShowFileUploadModal(true);
          } else if (a.selectedItem.text === 'New DMN File') {
            navigate(
              `/editor/process-models/${modifiedProcessModelId}/files?file_type=dmn`,
            );
          } else if (a.selectedItem.text === 'New JSON File') {
            navigate(
              `/process-models/${modifiedProcessModelId}/form?file_ext=json`,
            );
          } else if (a.selectedItem.text === 'New Markdown File') {
            navigate(
              `/process-models/${modifiedProcessModelId}/form?file_ext=md`,
            );
          }
        }}
        items={items}
        itemToString={(item: any) => (item ? item.text : '')}
      />
    );
  };

  return (
    <Tabs selectedIndex={selectedTabIndex} onChange={updateSelectedTab}>
      <TabList aria-label="List of tabs">
        <Tab>About</Tab>
        <Tab data-qa="process-model-files">Files</Tab>
        <Tab data-qa="process-instance-list-link">My process instances</Tab>
      </TabList>
      <TabPanels>
        <TabPanel>{/*  Placeholder, content provided by parent */}</TabPanel>
        <TabPanel>
          <Grid condensed fullWidth className="megacondensed">
            <Column md={6} lg={12} sm={4}>
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
            </Column>
          </Grid>
        </TabPanel>
        <TabPanel>
          {selectedTabIndex !== 2 ? null : (
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
          )}
        </TabPanel>
      </TabPanels>
    </Tabs>
  );
};

export default ProcessModelTabs;

