import { Routes, Route, useLocation } from 'react-router-dom';

import React, { useEffect } from 'react';
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
import Configuration from './Configuration';
import JsonSchemaFormBuilder from './JsonSchemaFormBuilder';
import ProcessModelNewExperimental from './ProcessModelNewExperimental';
import ProcessInstanceFindById from './ProcessInstanceFindById';
import ProcessInterstitialPage from './ProcessInterstitialPage';
import MessageListPage from './MessageListPage';

export default function EditorRoutes() {
  const location = useLocation();

  useEffect(() => {}, [location]);

  if (UserService.hasRole(['admin'])) {
    return (
      <div className="full-width-container">
        <Routes>
          <Route
            path="process-models/:process_model_id/files"
            element={<ProcessModelEditDiagram />}
          />
          <Route
            path="process-models/:process_model_id/files/:file_name"
            element={<ProcessModelEditDiagram />}
          />
        </Routes>
      </div>
    );
  }
  return (
    <main>
      <h1>404</h1>
    </main>
  );
}
