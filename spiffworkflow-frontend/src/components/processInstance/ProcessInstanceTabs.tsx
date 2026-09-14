import { useState } from 'react';
import { Box, Tab, Tabs } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { BasicTask, ProcessInstance } from '../../interfaces';
import TaskListTable from '../TaskListTable';
import ProcessInstanceLogList from '../ProcessInstanceLogList';
import MessageInstanceList from '../messages/MessageInstanceList';
import ProcessInstanceDiagramPanel from './ProcessInstanceDiagramPanel';
import ProcessInstanceSourceFiles from './ProcessInstanceSourceFiles';

type ProcessInstanceTabsProps = {
  processInstance: ProcessInstance;
  variant: string;
  modifiedProcessModelId: string;
  selectedTabIndex: number;
  selectedTaskTabSubTab: number;
  canViewLogs: boolean;
  canViewMsgs: boolean;
  tasks: BasicTask[] | null;
  tasksCallHadError: boolean;
  onSelectTab: (newTabIndex: number) => void;
  onSelectTaskSubTab: (newTabIndex: number) => void;
  onCallActivityNavigate: (task: BasicTask, event: any) => void;
  onElementClick: (shapeElement: any, bpmnProcessIdentifiers: any) => void;
};

function CompletedTasksSubTabs({
  processInstanceId,
  selectedTaskTabSubTab,
  onSelectTaskSubTab,
}: {
  processInstanceId: number;
  selectedTaskTabSubTab: number;
  onSelectTaskSubTab: (newTabIndex: number) => void;
}) {
  const { t } = useTranslation();
  return (
    <>
      <Tabs
        value={selectedTaskTabSubTab}
        onChange={(_, newValue) => onSelectTaskSubTab(newValue)}
      >
        <Tab label={t('completed_by_me_tab')} />
        <Tab label={t('all_completed_tab')} />
      </Tabs>
      <Box>
        {selectedTaskTabSubTab === 0 ? (
          <TaskListTable
            apiPath={`/tasks/completed-by-me/${processInstanceId}`}
            paginationClassName="with-large-bottom-margin"
            textToShowIfEmpty={t('no_completed_tasks_by_me')}
            shouldPaginateTable={false}
            showProcessModelIdentifier={false}
            showProcessId={false}
            showStartedBy={false}
            showTableDescriptionAsTooltip
            showDateStarted={false}
            showWaitingOn={false}
            canCompleteAllTasks={false}
            showViewFormDataButton
            defaultPerPage={20}
          />
        ) : null}
        {selectedTaskTabSubTab === 1 ? (
          <TaskListTable
            apiPath={`/tasks/completed/${processInstanceId}`}
            paginationClassName="with-large-bottom-margin"
            textToShowIfEmpty={t('no_completed_tasks')}
            shouldPaginateTable={false}
            showProcessModelIdentifier={false}
            showProcessId={false}
            showStartedBy={false}
            showTableDescriptionAsTooltip
            showDateStarted={false}
            showWaitingOn={false}
            canCompleteAllTasks={false}
            showCompletedBy
            showActionsColumn={false}
            defaultPerPage={20}
          />
        ) : null}
      </Box>
    </>
  );
}

export default function ProcessInstanceTabs({
  processInstance,
  variant,
  modifiedProcessModelId,
  selectedTabIndex,
  selectedTaskTabSubTab,
  canViewLogs,
  canViewMsgs,
  tasks,
  tasksCallHadError,
  onSelectTab,
  onSelectTaskSubTab,
  onCallActivityNavigate,
  onElementClick,
}: ProcessInstanceTabsProps) {
  const { t } = useTranslation();
  const [selectedSourcePath, setSelectedSourcePath] = useState('');
  return (
    <>
      <Tabs
        value={selectedTabIndex}
        onChange={(_, newValue) => onSelectTab(newValue)}
      >
        <Tab label={t('diagram_tab')} />
        <Tab label={t('milestones_tab')} disabled={!canViewLogs} />
        <Tab label={t('events_tab')} disabled={!canViewLogs} />
        <Tab label={t('messages')} disabled={!canViewMsgs} />
        <Tab label={t('tasks_tab')} />
        <Tab label={t('model_files_tab')} />
      </Tabs>
      <Box>
        {selectedTabIndex === 0 ? (
          <ProcessInstanceDiagramPanel
            processInstance={processInstance}
            tasks={tasks}
            tasksCallHadError={tasksCallHadError}
            modifiedProcessModelId={modifiedProcessModelId}
            onCallActivityNavigate={onCallActivityNavigate}
            onElementClick={onElementClick}
            onDecisionNavigate={(decisionId) => {
              const path = processInstance.decision_source_paths?.[decisionId];
              if (!path) {
                return false;
              }
              setSelectedSourcePath(path);
              onSelectTab(5);
              return true;
            }}
          />
        ) : null}
        {selectedTabIndex === 1 ? (
          <ProcessInstanceLogList
            variant={variant}
            isEventsView={false}
            modifiedProcessModelId={modifiedProcessModelId}
            processInstanceId={processInstance.id}
          />
        ) : null}
        {selectedTabIndex === 2 ? (
          <ProcessInstanceLogList
            variant={variant}
            isEventsView
            modifiedProcessModelId={modifiedProcessModelId}
            processInstanceId={processInstance.id}
          />
        ) : null}
        {selectedTabIndex === 3 && canViewMsgs ? (
          <MessageInstanceList processInstanceId={processInstance.id} />
        ) : null}
        {selectedTabIndex === 4 ? (
          <CompletedTasksSubTabs
            processInstanceId={processInstance.id}
            selectedTaskTabSubTab={selectedTaskTabSubTab}
            onSelectTaskSubTab={onSelectTaskSubTab}
          />
        ) : null}
        {selectedTabIndex === 5 ? (
          <ProcessInstanceSourceFiles
            key={`${processInstance.id}:${processInstance.source_manifest_id}`}
            files={processInstance.source_files || []}
            apiPath={`/process-instances${variant === 'all' ? '' : '/for-me'}/${modifiedProcessModelId}/${processInstance.id}`}
            selectedPath={selectedSourcePath}
            onSelectPath={setSelectedSourcePath}
          />
        ) : null}
      </Box>
    </>
  );
}
