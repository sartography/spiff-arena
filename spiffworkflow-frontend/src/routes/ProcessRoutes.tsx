import { useEffect, useState } from 'react';
import { Route, Routes, useLocation, useNavigate } from 'react-router-dom';
// @ts-ignore
import { Tabs, TabList, Tab } from '@carbon/react';
import TaskShow from './TaskShow';
import MyTasks from './MyTasks';
import GroupedTasks from './GroupedTasks';
import CompletedInstances from './CompletedInstances';
import CreateNewInstance from './CreateNewInstance';
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
