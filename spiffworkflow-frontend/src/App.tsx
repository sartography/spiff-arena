import { useMemo, useState } from 'react';
// @ts-ignore
import { Content } from '@carbon/react';

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import ErrorContext from './contexts/ErrorContext';
import NavigationBar from './components/NavigationBar';

import HomePage from './routes/HomePage';
import TaskShow from './routes/TaskShow';
import ErrorBoundary from './components/ErrorBoundary';
import AdminRoutes from './routes/AdminRoutes';
import { ErrorForDisplay } from './interfaces';

export default function App() {
  const [errorMessage, setErrorMessage] = useState<ErrorForDisplay | null>(
    null
  );

  const errorContextValueArray = useMemo(
    () => [errorMessage, setErrorMessage],
    [errorMessage]
  );

  let errorTag = null;
  if (errorMessage) {
    let sentryLinkTag = null;
    if (errorMessage.sentry_link) {
      sentryLinkTag = (
        <span>
          {
            ': Find details about this error here (it may take a moment to become available): '
          }
          <a href={errorMessage.sentry_link} target="_blank" rel="noreferrer">
            {errorMessage.sentry_link}
          </a>
        </span>
      );
    }
    errorTag = (
      <div id="filter-errors" className="mt-4 alert alert-danger" role="alert">
        {errorMessage.message}
        {sentryLinkTag}
      </div>
    );
  }

  return (
    <div className="cds--white">
      <ErrorContext.Provider value={errorContextValueArray}>
        <BrowserRouter>
          <NavigationBar />
          <Content>
            {errorTag}
            <ErrorBoundary>
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/tasks" element={<HomePage />} />
                <Route path="/admin/*" element={<AdminRoutes />} />
                <Route
                  path="/tasks/:process_instance_id/:task_id"
                  element={<TaskShow />}
                />
                <Route
                  path="/tasks/:process_instance_id/:task_id"
                  element={<TaskShow />}
                />
              </Routes>
            </ErrorBoundary>
          </Content>
        </BrowserRouter>
      </ErrorContext.Provider>
    </div>
  );
}
