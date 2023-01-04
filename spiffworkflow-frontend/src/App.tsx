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
import ErrorDisplay from './components/ErrorDisplay';

export default function App() {
  const [errorObject, setErrorObject] = useState<ErrorForDisplay | null>(null);

  const errorContextValueArray = useMemo(
    () => [errorObject, setErrorObject],
    [errorObject]
  );

  if (!UserService.isLoggedIn()) {
    UserService.doLogin();
    return null;
  }

  const ability = defineAbility(() => {});

  return (
    <div className="cds--white">
      {/* @ts-ignore */}
      <AbilityContext.Provider value={ability}>
        <ErrorContext.Provider value={errorContextValueArray}>
          <BrowserRouter>
            <NavigationBar />
            <Content>
              <ErrorDisplay />
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
