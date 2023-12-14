import { Route, Routes } from 'react-router-dom';
import DataStoreList from './DataStoreList';
import DataStoreNew from './DataStoreNew';

export default function DataStoreRoutes() {
  return (
    <Routes>
      <Route path="/" element={<DataStoreList />} />
      <Route path="new" element={<DataStoreNew />} />
    </Routes>
  );
}
