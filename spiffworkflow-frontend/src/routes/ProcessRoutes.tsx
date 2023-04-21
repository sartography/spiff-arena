import { Route, Routes } from 'react-router-dom';
// @ts-ignore
import ProcessInterstitial from './ProcessInterstitial';

export default function ProcessRoutes() {
  return (
    <Routes>
      <Route
        path=":process_model_identifier/:process_instance_id/interstitial"
        element={<ProcessInterstitial />}
      />
    </Routes>
  );
}
