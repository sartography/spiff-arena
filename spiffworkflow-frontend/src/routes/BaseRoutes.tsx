import { Route, Routes } from 'react-router-dom';
import { Loading } from '@carbon/react';
import Configuration from './Configuration';
import MessageListPage from './MessageListPage';
import DataStoreRoutes from './DataStoreRoutes';
import { UiSchemaUxElement } from '../extension_ui_schema_interfaces';
import HomeRoutes from './HomeRoutes';
import ProcessGroupRoutes from './ProcessGroupRoutes';
import ProcessModelRoutes from './ProcessModelRoutes';
import ProcessInstanceRoutes from './ProcessInstanceRoutes';
import ErrorDisplay from '../components/ErrorDisplay';
import ProcessInstanceShortLink from './ProcessInstanceShortLink';
import About from './About';
import Page404 from './Page404';
import AdminRedirect from './AdminRedirect';
import RootRoute from './RootRoute';
import LoginHandler from '../components/LoginHandler';
import { ExtensionUxElementMap } from '../components/ExtensionUxElementForDisplay';
import Extension from './Extension';

type OwnProps = {
  extensionUxElements?: UiSchemaUxElement[] | null;
};

export default function BaseRoutes({ extensionUxElements }: OwnProps) {
  const elementCallback = (uxElement: UiSchemaUxElement) => {
    return (
      <Route
        path={uxElement.page}
        key={uxElement.page}
        element={<Extension pageIdentifier={uxElement.page} />}
      />
    );
  };

  if (extensionUxElements !== null) {
    const extensionRoutes = ExtensionUxElementMap({
      displayLocation: 'routes',
      elementCallback,
      extensionUxElements,
    });

    return (
      <div className="fixed-width-container">
        <ErrorDisplay />
        <LoginHandler />
        <Routes>
          {extensionRoutes}
          <Route path="/" element={<RootRoute />} />
          <Route path="tasks/*" element={<HomeRoutes />} />
          <Route path="process-groups/*" element={<ProcessGroupRoutes />} />
          <Route path="process-models/*" element={<ProcessModelRoutes />} />
          <Route
            path="process-instances/*"
            element={<ProcessInstanceRoutes />}
          />
          <Route
            path="i/:process_instance_id"
            element={<ProcessInstanceShortLink />}
          />
          <Route
            path="configuration/*"
            element={
              <Configuration extensionUxElements={extensionUxElements} />
            }
          />
          <Route path="messages" element={<MessageListPage />} />
          <Route path="data-stores/*" element={<DataStoreRoutes />} />
          <Route path="about" element={<About />} />
          <Route path="admin/*" element={<AdminRedirect />} />
          <Route path="/*" element={<Page404 />} />
        </Routes>
      </div>
    );
  }

  const style = { margin: '50px 0 50px 50px' };
  return (
    <div className="fixed-width-container">
      <Loading
        description="Active loading indicator"
        withOverlay={false}
        style={style}
      />
    </div>
  );
}
