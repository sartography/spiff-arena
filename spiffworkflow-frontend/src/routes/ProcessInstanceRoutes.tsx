import { Route, Routes } from 'react-router-dom';
import ProcessInstanceList from './ProcessInstanceList';
import ProcessInstanceShow from './ProcessInstanceShow';
import ProcessInstanceReportList from './ProcessInstanceReportList';
import ProcessInstanceReportNew from './ProcessInstanceReportNew';
import ProcessInstanceReportEdit from './ProcessInstanceReportEdit';
import ProcessInstanceFindById from './ProcessInstanceFindById';
import ProcessInterstitialPage from './ProcessInterstitialPage';
import ProcessInstanceProgressPage from './ProcessInstanceProgressPage';
import ProcessInstanceMigratePage from './ProcessInstanceMigratePage';

export default function ProcessInstanceRoutes() {
  return (
    <Routes>
      <Route path="/" element={<ProcessInstanceList variant="for-me" />} />
      <Route path="for-me" element={<ProcessInstanceList variant="for-me" />} />
      <Route path="all" element={<ProcessInstanceList variant="all" />} />
      <Route
        path="for-me/:process_model_id/:process_instance_id"
        element={<ProcessInstanceShow variant="for-me" />}
      />
      <Route
        path="for-me/:process_model_id/:process_instance_id/:to_task_guid"
        element={<ProcessInstanceShow variant="for-me" />}
      />
      <Route
        path="for-me/:process_model_id/:process_instance_id/interstitial"
        element={<ProcessInterstitialPage variant="for-me" />}
      />
      <Route
        path=":process_model_id/:process_instance_id/interstitial"
        element={<ProcessInterstitialPage variant="all" />}
      />
      <Route
        path="for-me/:process_model_id/:process_instance_id/progress"
        element={<ProcessInstanceProgressPage variant="for-me" />}
      />
      <Route
        path=":process_model_id/:process_instance_id/progress"
        element={<ProcessInstanceProgressPage variant="all" />}
      />
      <Route
        path=":process_model_id/:process_instance_id/migrate"
        element={<ProcessInstanceMigratePage />}
      />
      <Route
        path=":process_model_id/:process_instance_id"
        element={<ProcessInstanceShow variant="all" />}
      />
      <Route
        path=":process_model_id/:process_instance_id/:to_task_guid"
        element={<ProcessInstanceShow variant="all" />}
      />
      <Route path="reports" element={<ProcessInstanceReportList />} />
      <Route path="reports/new" element={<ProcessInstanceReportNew />} />
      <Route
        path="reports/:report_identifier/edit"
        element={<ProcessInstanceReportEdit />}
      />
      <Route path="find-by-id" element={<ProcessInstanceFindById />} />
    </Routes>
  );
}
