import { defineAbility } from '@casl/ability';
import React from 'react';

import { createBrowserRouter, Outlet, RouterProvider } from 'react-router-dom';
import { AbilityContext } from './contexts/Can';
import APIErrorProvider from './contexts/APIErrorContext';
import ContainerForExtensions from './ContainerForExtensions';
import PublicRoutes from './routes/PublicRoutes';

export default function App() {
  const ability = defineAbility(() => {});
  const routeComponents = () => {
    return [
      {
        path: '*',
        element: <ContainerForExtensions />,
      },
      { path: 'public/*', element: <PublicRoutes /> },
    ];
  };

  const layout = () => {
    return (
      <div className="cds--white">
        <APIErrorProvider>
          <AbilityContext.Provider value={ability}>
            <Outlet />;
          </AbilityContext.Provider>
        </APIErrorProvider>
      </div>
    );
  };
  const router = createBrowserRouter([
    {
      path: '*',
      Component: layout,
      children: routeComponents(),
    },
  ]);
  return <RouterProvider router={router} />;
}
