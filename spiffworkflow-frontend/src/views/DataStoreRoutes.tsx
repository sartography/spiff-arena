import { Route, Routes } from 'react-router-dom';
import DataStoreList from './DataStoreList';
import DataStoreNew from './DataStoreNew';
import DataStoreEdit from './DataStoreEdit';

export default function DataStoreRoutes() {
  return (
    <Routes>
      <Route path="/" element={<DataStoreList />} />
      <Route path=":data_store_identifier/edit" element={<DataStoreEdit />} />
      <Route path="new" element={<DataStoreNew />} />
    </Routes>
  );
}
