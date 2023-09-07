import { Routes, Route, useLocation } from 'react-router-dom';

import React, { useEffect } from 'react';
import ProcessModelEditDiagram from './ProcessModelEditDiagram';
import UserService from '../services/UserService';

export default function EditorRoutes() {
  const location = useLocation();

  useEffect(() => {}, [location]);

  if (UserService.hasRole(['admin'])) {
    return (
      <div className="full-width-container no-center-stuff">
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
