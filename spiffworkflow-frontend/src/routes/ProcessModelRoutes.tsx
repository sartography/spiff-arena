import { Route, Routes } from 'react-router-dom';
import ProcessModelEdit from './ProcessModelEdit';
import ProcessModelNew from './ProcessModelNew';
import ProcessModelNewExperimental from './ProcessModelNewExperimental';
import ProcessModelShow from './ProcessModelShow';
import ReactFormEditor from './ReactFormEditor';

export default function ProcessModelRoutes() {
  return (
    <Routes>
      <Route path=":process_group_id/new" element={<ProcessModelNew />} />
      <Route
        path=":process_group_id/new-e"
        element={<ProcessModelNewExperimental />}
      />
      <Route path=":process_model_id" element={<ProcessModelShow />} />
      <Route path=":process_model_id/edit" element={<ProcessModelEdit />} />
      <Route path=":process_model_id/form" element={<ReactFormEditor />} />
      <Route
        path=":process_model_id/form/:file_name"
        element={<ReactFormEditor />}
      />
    </Routes>
  );
}
