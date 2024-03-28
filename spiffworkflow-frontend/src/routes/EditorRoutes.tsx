import { useLocation, Routes, Route } from 'react-router-dom';

import React, { useEffect } from 'react';
import ErrorDisplay from '../components/ErrorDisplay';
import LoginHandler from '../components/LoginHandler';
import ProcessModelEditDiagram from './ProcessModelEditDiagram';

export default function EditorRoutes() {
  const location = useLocation();

  useEffect(() => {}, [location]);

  return (
    <div className="full-width-container no-center-stuff">
      <ErrorDisplay />
      <LoginHandler />
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
