import { Route, Routes } from 'react-router-dom';
// @ts-ignore
import ProcessInterstitialPage from './ProcessInterstitialPage';

export default function ProcessRoutes() {
  return (
    <Routes>
      <Route
        path=":modified_process_model_identifier/:process_instance_id/interstitial"
        element={<ProcessInterstitialPage />}
      />
    </Routes>
  );
}
