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

type OwnProps = {
  extensionUxElements?: UiSchemaUxElement[] | null;
};

export default function BaseRoutes({ extensionUxElements }: OwnProps) {
  return (
    <div className="fixed-width-container">
      <ErrorDisplay />
      <Routes>
        <Route path="/" element={<HomeRoutes />} />
        <Route path="tasks/*" element={<HomeRoutes />} />
        <Route path="process-groups/*" element={<ProcessGroupRoutes />} />
        <Route path="process-models/*" element={<ProcessModelRoutes />} />
        <Route path="process-instances/*" element={<ProcessInstanceRoutes />} />
        <Route
          path="configuration/*"
          element={<Configuration extensionUxElements={extensionUxElements} />}
        />
        <Route path="messages" element={<MessageListPage />} />
        <Route path="data-stores" element={<DataStorePage />} />
      </Routes>
    </div>
  );
}
