import React, { useState } from 'react';
import { Box } from '@mui/material';
import { Route, Routes } from 'react-router';
import Homepage from './Homepage';
import '../assets/styles/transitions.css';
import Processes from './StartProcess/Processes';
import StartProcessInstance from './StartProcess/StartProcessInstance';
import InstancesStartedByMe from './InstancesStartedByMe';
import TaskShow from './TaskShow/TaskShow';
import ProcessInterstitialPage from './TaskShow/ProcessInterstitialPage';
import ProcessInstanceProgressPage from './TaskShow/ProcessInstanceProgressPage';
import ErrorDisplay from '../components/ErrorDisplay';
import About from './About';
import MessageListPage from './MessageListPage';
import DataStoreRoutes from './DataStoreRoutes';
import Configuration from './Configuration';
import AuthenticationList from './AuthenticationList';
import SecretList from './SecretList';
import SecretNew from './SecretNew';
import SecretShow from './SecretShow';
import ProcessModelShow from './ProcessModelShow';
import ProcessModelNew from './ProcessModelNew';
import ProcessModelEdit from './ProcessModelEdit'; // Import the edited component
import ProcessModelEditDiagram from './ProcessModelEditDiagram';
import ReactFormEditor from './ReactFormEditor'; // Import the new component
import ProcessInstanceRoutes from './ProcessInstanceRoutes';
import ProcessInstanceShortLink from './ProcessInstanceShortLink';
// Import the new component
import { UiSchemaUxElement } from '../extension_ui_schema_interfaces';
import { extensionUxElementMap } from '../components/ExtensionUxElementForDisplay';
import Extension from './Extension';
import ProcessGroupNew from './ProcessGroupNew';
import ProcessGroupEdit from './ProcessGroupEdit';
import ProcessModelNewExperimental from './ProcessModelNewExperimental';

type OwnProps = {
  setAdditionalNavElement: Function;
  extensionUxElements?: UiSchemaUxElement[] | null;
  isMobile?: boolean;
};

export default function BaseRoutes({
  extensionUxElements,
  setAdditionalNavElement,
  isMobile = false,
}: OwnProps) {
  const [viewMode, setViewMode] = useState<'table' | 'tile'>(
    isMobile ? 'tile' : 'table',
  );
  const elementCallback = (uxElement: UiSchemaUxElement) => {
    return (
      <Route
        path={uxElement.page}
        key={uxElement.page}
        element={<Extension pageIdentifier={uxElement.page} />}
      />
    );
  };
  const extensionRoutes = extensionUxElementMap({
    displayLocation: 'routes',
    elementCallback,
    extensionUxElements,
  });

  return (
    <Box
      component="main"
      sx={{
        flexGrow: 1,
        p: 3,
        overflow: 'auto',
        height: 'unset',
      }}
    >
      <ErrorDisplay />
      <Routes>
        {extensionRoutes}
        <Route path="/about" element={<About />} />
        <Route
          path="/"
          element={
            <Homepage
              viewMode={viewMode}
              setViewMode={setViewMode}
              isMobile={isMobile}
            />
          }
        />
        <Route
          path="/process-groups"
          element={
            <Processes setNavElementCallback={setAdditionalNavElement} />
          }
        />
        <Route
          path="/process-groups/:process_group_id"
          element={
            <Processes setNavElementCallback={setAdditionalNavElement} />
          }
        />
        <Route
          path="/process-models/:process_model_id"
          element={<ProcessModelShow />}
        />
        <Route
          path="/:modifiedProcessModelId/start"
          element={<StartProcessInstance />}
        />
        <Route
          path="/tasks/:process_instance_id/:task_guid"
          element={<TaskShow />}
        />
        <Route
          path="/started-by-me"
          element={
            <InstancesStartedByMe
              viewMode={viewMode}
              setViewMode={setViewMode}
              isMobile={isMobile}
            />
          }
        />
        <Route
          path="process-instances/for-me/:process_model_id/:process_instance_id/interstitial"
          element={<ProcessInterstitialPage variant="for-me" />}
        />
        <Route
          path="process-instances/for-me/:process_model_id/:process_instance_id/progress"
          element={<ProcessInstanceProgressPage variant="for-me" />}
        />
        <Route path="/messages" element={<MessageListPage />} />
        <Route path="/data-stores/*" element={<DataStoreRoutes />} />
        <Route
          path="/configuration/*"
          element={<Configuration extensionUxElements={extensionUxElements} />}
        />
        <Route path="/authentication-list" element={<AuthenticationList />} />
        <Route path="/secrets" element={<SecretList />} />{' '}
        <Route path="/secrets/new" element={<SecretNew />} />
        <Route path="/secrets/:secret_identifier" element={<SecretShow />} />
        <Route
          path=":process_group_id/new-e"
          element={<ProcessModelNewExperimental />}
        />
        <Route
          path="/process-models/:process_group_id/new"
          element={<ProcessModelNew />}
        />
        <Route
          path="/process-models/:process_model_id/edit"
          element={<ProcessModelEdit />}
        />
        <Route
          path="/process-models/:process_model_id/files/:file_name"
          element={<ProcessModelEditDiagram />}
        />
        <Route
          path="/process-models/:process_model_id/files"
          element={<ProcessModelEditDiagram />}
        />
        <Route
          path="/process-models/:process_model_id/form/:file_name"
          element={<ReactFormEditor />}
        />
        <Route
          path="/process-models/:process_model_id/form"
          element={<ReactFormEditor />}
        />
        <Route path="process-instances/*" element={<ProcessInstanceRoutes />} />
        <Route
          path="i/:process_instance_id"
          element={<ProcessInstanceShortLink />}
        />
        <Route path="/process-groups/new" element={<ProcessGroupNew />} />
        <Route
          path="/process-groups/:process_group_id/edit"
          element={<ProcessGroupEdit />}
        />
      </Routes>
    </Box>
  );
}
