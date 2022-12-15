import { useMemo, useState } from 'react';
// @ts-ignore
import { Content } from '@carbon/react';

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { defineAbility } from '@casl/ability';
import ErrorContext from './contexts/ErrorContext';
import NavigationBar from './components/NavigationBar';

import HomePageRoutes from './routes/HomePageRoutes';
import ErrorBoundary from './components/ErrorBoundary';
import AdminRoutes from './routes/AdminRoutes';
import { ErrorForDisplay } from './interfaces';

import { AbilityContext } from './contexts/Can';
import UserService from './services/UserService';

export default function App() {
  const [errorMessage, setErrorMessage] = useState<ErrorForDisplay | null>(
    null
  );

  const errorContextValueArray = useMemo(
    () => [errorMessage, setErrorMessage],
    [errorMessage]
  );

  if (!UserService.isLoggedIn()) {
    UserService.doLogin();
    return null;
  }

  const ability = defineAbility(() => {});

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
      {/* @ts-ignore */}
      <AbilityContext.Provider value={ability}>
        <ErrorContext.Provider value={errorContextValueArray}>
          <BrowserRouter>
            <NavigationBar />
            <Content>
              {errorTag}
              <ErrorBoundary>
                <Routes>
                  <Route path="/*" element={<HomePageRoutes />} />
                  <Route path="/tasks/*" element={<HomePageRoutes />} />
                  <Route path="/admin/*" element={<AdminRoutes />} />
                </Routes>
              </ErrorBoundary>
            </Content>
          </BrowserRouter>
        </ErrorContext.Provider>
      </AbilityContext.Provider>
    </div>
  );
}
