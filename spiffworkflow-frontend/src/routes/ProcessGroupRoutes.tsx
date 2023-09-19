import { Route, Routes } from 'react-router-dom';
import ProcessGroupList from './ProcessGroupList';
import ProcessGroupShow from './ProcessGroupShow';
import ProcessGroupNew from './ProcessGroupNew';
import ProcessGroupEdit from './ProcessGroupEdit';

export default function ProcessGroupRoutes() {
  return (
    <Routes>
      <Route path="/" element={<ProcessGroupList />} />
      <Route path="/:process_group_id" element={<ProcessGroupShow />} />
      <Route path="new" element={<ProcessGroupNew />} />
      <Route path=":process_group_id/edit" element={<ProcessGroupEdit />} />
    </Routes>
  );
}
