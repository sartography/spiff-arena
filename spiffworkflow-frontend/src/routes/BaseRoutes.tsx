import { Route, Routes } from 'react-router-dom';
import Configuration from './Configuration';
import MessageListPage from './MessageListPage';
import DataStorePage from './DataStorePage';
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

type OwnProps = {
  extensionUxElements?: UiSchemaUxElement[] | null;
};

export default function BaseRoutes({ extensionUxElements }: OwnProps) {
  return (
    <div className="fixed-width-container">
      <ErrorDisplay />
      <LoginHandler />
      <Routes>
        <Route path="/" element={<RootRoute />} />
        <Route path="tasks/*" element={<HomeRoutes />} />
        <Route path="process-groups/*" element={<ProcessGroupRoutes />} />
        <Route path="process-models/*" element={<ProcessModelRoutes />} />
        <Route path="process-instances/*" element={<ProcessInstanceRoutes />} />
        <Route
          path="i/:process_instance_id"
          element={<ProcessInstanceShortLink />}
        />
        <Route
          path="configuration/*"
          element={<Configuration extensionUxElements={extensionUxElements} />}
        />
        <Route path="messages" element={<MessageListPage />} />
        <Route path="data-stores" element={<DataStorePage />} />
        <Route path="about" element={<About />} />
        <Route path="admin/*" element={<AdminRedirect />} />
        <Route path="/*" element={<Page404 />} />
      </Routes>
    </div>
  );
}
