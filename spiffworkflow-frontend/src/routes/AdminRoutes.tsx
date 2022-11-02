import { Routes, Route, useLocation } from 'react-router-dom';

import { useContext, useEffect } from 'react';
import ProcessGroupList from './ProcessGroupList';
import ProcessGroupShow from './ProcessGroupShow';
import ProcessGroupNew from './ProcessGroupNew';
import ProcessGroupEdit from './ProcessGroupEdit';
import ProcessModelShow from './ProcessModelShow';
import ProcessModelEditDiagram from './ProcessModelEditDiagram';
import ProcessInstanceList from './ProcessInstanceList';
import ProcessInstanceReportShow from './ProcessInstanceReportShow';
import ProcessModelNew from './ProcessModelNew';
import ProcessModelEdit from './ProcessModelEdit';
import ProcessInstanceShow from './ProcessInstanceShow';
import UserService from '../services/UserService';
import ProcessInstanceReportList from './ProcessInstanceReportList';
import ProcessInstanceReportNew from './ProcessInstanceReportNew';
import ProcessInstanceReportEdit from './ProcessInstanceReportEdit';
import ReactFormEditor from './ReactFormEditor';
import ErrorContext from '../contexts/ErrorContext';
import ProcessInstanceLogList from './ProcessInstanceLogList';
import MessageInstanceList from './MessageInstanceList';
import SecretList from './SecretList';
import SecretNew from './SecretNew';
import SecretShow from './SecretShow';
import AuthenticationList from './AuthenticationList';

export default function AdminRoutes() {
  const location = useLocation();
  const setErrorMessage = (useContext as any)(ErrorContext)[1];

  useEffect(() => {
    setErrorMessage(null);
  }, [location, setErrorMessage]);

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
          path="process-models/:process_group_id/:process_model_id"
          element={<ProcessModelShow />}
        />
        <Route
          path="process-models/:process_group_id/:process_model_id/files"
          element={<ProcessModelEditDiagram />}
        />
        <Route
          path="process-models/:process_group_id/:process_model_id/files/:file_name"
          element={<ProcessModelEditDiagram />}
        />
        <Route
          path="process-models/:process_group_id/:process_model_id/process-instances"
          element={<ProcessInstanceList />}
        />
        <Route
          path="process-models/:process_group_id/:process_model_id/edit"
          element={<ProcessModelEdit />}
        />
        <Route
          path="process-models/:process_group_id/:process_model_id/process-instances/:process_instance_id"
          element={<ProcessInstanceShow />}
        />
        <Route
          path="process-models/:process_group_id/:process_model_id/process-instances/:process_instance_id/:spiff_step"
          element={<ProcessInstanceShow />}
        />
        <Route
          path="process-models/:process_group_id/:process_model_id/process-instances/reports"
          element={<ProcessInstanceReportList />}
        />
        <Route
          path="process-models/:process_group_id/:process_model_id/process-instances/reports/:report_identifier"
          element={<ProcessInstanceReportShow />}
        />
        <Route
          path="process-models/:process_group_id/:process_model_id/process-instances/reports/new"
          element={<ProcessInstanceReportNew />}
        />
        <Route
          path="process-models/:process_group_id/:process_model_id/process-instances/reports/:report_identifier/edit"
          element={<ProcessInstanceReportEdit />}
        />
        <Route
          path="process-models/:process_group_id/:process_model_id/form"
          element={<ReactFormEditor />}
        />
        <Route
          path="process-models/:process_group_id/:process_model_id/form/:file_name"
          element={<ReactFormEditor />}
        />
        <Route
          path="process-models/:process_group_id/:process_model_id/process-instances/:process_instance_id/logs"
          element={<ProcessInstanceLogList />}
        />
        <Route path="process-instances" element={<ProcessInstanceList />} />
        <Route path="messages" element={<MessageInstanceList />} />
        <Route path="secrets" element={<SecretList />} />
        <Route path="secrets/new" element={<SecretNew />} />
        <Route path="secrets/:key" element={<SecretShow />} />
        <Route path="authentications" element={<AuthenticationList />} />
      </Routes>
    );
  }
  return (
    <main>
      <h1>404</h1>
    </main>
  );
}
