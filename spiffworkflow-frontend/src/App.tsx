// @ts-ignore
import { Content } from '@carbon/react';

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { defineAbility } from '@casl/ability';
import React from 'react';
import NavigationBar from './components/NavigationBar';

import HomePageRoutes from './routes/HomePageRoutes';
import About from './routes/About';
import ErrorBoundary from './components/ErrorBoundary';
import AdminRoutes from './routes/AdminRoutes';

import { AbilityContext } from './contexts/Can';
import UserService from './services/UserService';
import APIErrorProvider from './contexts/APIErrorContext';
import ScrollToTop from './components/ScrollToTop';
import EditorRoutes from './routes/EditorRoutes';
import Extension from './routes/Extension';

export default function App() {
  if (!UserService.isLoggedIn()) {
    UserService.doLogin();
    return null;
  }

  const ability = defineAbility(() => {});

  let contentClassName = 'main-site-body-centered';
  if (window.location.pathname.startsWith('/editor/')) {
    contentClassName = 'no-center-stuff';
  }

  return (
    <div className="cds--white">
      {/* @ts-ignore */}
      <AbilityContext.Provider value={ability}>
        <APIErrorProvider>
          <BrowserRouter>
            <NavigationBar />
            <Content className={contentClassName}>
              <ScrollToTop />
              <ErrorBoundary>
                <Routes>
                  <Route path="/*" element={<HomePageRoutes />} />
                  <Route path="/about" element={<About />} />
                  <Route path="/tasks/*" element={<HomePageRoutes />} />
                  <Route path="/admin/*" element={<AdminRoutes />} />
                  <Route path="/editor/*" element={<EditorRoutes />} />
                  <Route
                    path="/extensions/:process_model"
                    element={<Extension />}
                  />
                  <Route
                    path="/extensions/:process_model/:extension_route"
                    element={<Extension />}
                  />
                </Routes>
              </ErrorBoundary>
            </Content>
          </BrowserRouter>
        </APIErrorProvider>
      </AbilityContext.Provider>
    </div>
  );
}
