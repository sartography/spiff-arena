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
import { Notification } from './components/Notification';
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

  // let errorTag = null;
  // if (errorObject) {
  //   let sentryLinkTag = null;
  //   if (errorObject.sentry_link) {
  //     sentryLinkTag = (
  //       <span>
  //         {
  //           ': Find details about this error here (it may take a moment to become available): '
  //         }
  //         <a href={errorObject.sentry_link} target="_blank" rel="noreferrer">
  //           {errorObject.sentry_link}
  //         </a>
  //       </span>
  //     );
  //   }
  //
  //   let message = <div>{errorObject.message}</div>;
  //   let title = 'Error:';
  //   if ('task_name' in errorObject && errorObject.task_name) {
  //     title = 'Error in python script:';
  //     message = (
  //       <>
  //         <br />
  //         <div>
  //           Task: {errorObject.task_name} ({errorObject.task_id})
  //         </div>
  //         <div>File name: {errorObject.file_name}</div>
  //         <div>Line number in script task: {errorObject.line_number}</div>
  //         <br />
  //         <div>{errorObject.message}</div>
  //       </>
  //     );
  //   }
  //
  //   errorTag = (
  //     <Notification
  //       title={title}
  //       onClose={() => setErrorObject(null)}
  //       type="error"
  //     >
  //       {message}
  //       {sentryLinkTag}
  //     </Notification>
  //   );
  // }

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
