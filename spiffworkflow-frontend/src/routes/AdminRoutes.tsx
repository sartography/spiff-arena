import { Routes, Route, useLocation } from 'react-router-dom';

import { useEffect } from 'react';
import ProcessGroupList from './ProcessGroupList';
import ProcessGroupShow from './ProcessGroupShow';
import ProcessGroupNew from './ProcessGroupNew';
import ProcessGroupEdit from './ProcessGroupEdit';
import ProcessModelShow from './ProcessModelShow';
import ProcessModelEditDiagram from './ProcessModelEditDiagram';
import ProcessInstanceList from './ProcessInstanceList';
import ProcessModelNew from './ProcessModelNew';
import ProcessModelEdit from './ProcessModelEdit';
import ProcessInstanceShow from './ProcessInstanceShow';
import UserService from '../services/UserService';
import ProcessInstanceReportList from './ProcessInstanceReportList';
import ProcessInstanceReportNew from './ProcessInstanceReportNew';
import ProcessInstanceReportEdit from './ProcessInstanceReportEdit';
import ReactFormEditor from './ReactFormEditor';
import ProcessInstanceLogList from './ProcessInstanceLogList';
import MessageInstanceList from './MessageInstanceList';
import Configuration from './Configuration';
import JsonSchemaFormBuilder from './JsonSchemaFormBuilder';
import ProcessModelNewExperimental from './ProcessModelNewExperimental';
import ProcessInstanceFindById from './ProcessInstanceFindById';
import ProcessInterstitialPage from "./ProcessInterstitialPage";

export default function AdminRoutes() {
  const location = useLocation();

  useEffect(() => {}, [location]);

  if (UserService.hasRole(['admin'])) {
    return (
      <Routes>
        <Route path="/" element={<ProcessGroupList />} />
        <Route path="process-groups" element={<ProcessGroupList />} />
        <Route
          path="process-groups/:process_group_id"
          element={<ProcessGroupShow />}
        />
        <Route path="process-groups/new" element={<ProcessGroupNew />} />
        <Route
          path="process-groups/:process_group_id/edit"
          element={<ProcessGroupEdit />}
        />

        <Route
          path="process-models/:process_group_id/new"
          element={<ProcessModelNew />}
        />
        <Route
          path="process-models/:process_group_id/new-e"
          element={<ProcessModelNewExperimental />}
        />
        <Route
          path="process-models/:process_model_id"
          element={<ProcessModelShow />}
        />
        <Route
          path="process-models/:process_model_id/files"
          element={<ProcessModelEditDiagram />}
        />
        <Route
          path="process-models/:process_model_id/files/:file_name"
          element={<ProcessModelEditDiagram />}
        />
        <Route
          path="process-models/:process_model_id/edit"
          element={<ProcessModelEdit />}
        />
        <Route
          path="process-instances/for-me/:process_model_id/:process_instance_id"
          element={<ProcessInstanceShow variant="for-me" />}
        />
        <Route
          path="process-instances/for-me/:process_model_id/:process_instance_id/:to_task_guid"
          element={<ProcessInstanceShow variant="for-me" />}
        />
        <Route
          path="process-instances/for-me/:process_model_id/:process_instance_id/interstitial"
          element={<ProcessInterstitialPage variant="for-me" />}
        />
        <Route
          path="process-instances/:process_model_id/:process_instance_id/interstitial"
          element={<ProcessInterstitialPage variant="all" />}
        />
        <Route
          path="process-instances/:process_model_id/:process_instance_id"
          element={<ProcessInstanceShow variant="all" />}
        />
        <Route
          path="process-instances/:process_model_id/:process_instance_id/:to_task_guid"
          element={<ProcessInstanceShow variant="all" />}
        />
        <Route
          path="process-instances/reports"
          element={<ProcessInstanceReportList />}
        />
        <Route
          path="process-instances/reports/new"
          element={<ProcessInstanceReportNew />}
        />
        <Route
          path="process-instances/reports/:report_identifier/edit"
          element={<ProcessInstanceReportEdit />}
        />
        <Route
          path="process-models/:process_model_id/form"
          element={<ReactFormEditor />}
        />
        <Route
          path="process-models/:process_model_id/form/:file_name"
          element={<ReactFormEditor />}
        />
        <Route
          path="logs/:process_model_id/:process_instance_id"
          element={<ProcessInstanceLogList variant="all" />}
        />
        <Route
          path="logs/for-me/:process_model_id/:process_instance_id"
          element={<ProcessInstanceLogList variant="for-me" />}
        />
        <Route
          path="process-instances"
          element={<ProcessInstanceList variant="for-me" />}
        />
        <Route
          path="process-instances/for-me"
          element={<ProcessInstanceList variant="for-me" />}
        />
        <Route
          path="process-instances/all"
          element={<ProcessInstanceList variant="all" />}
        />
        <Route path="messages" element={<MessageInstanceList />} />
        <Route path="configuration/*" element={<Configuration />} />
        <Route
          path="process-models/:process_model_id/form-builder"
          element={<JsonSchemaFormBuilder />}
        />
        <Route
          path="process-instances/find-by-id"
          element={<ProcessInstanceFindById />}
        />
      </Routes>
    );
  }
  return (
    <main>
      <h1>404</h1>
    </main>
  );
}
