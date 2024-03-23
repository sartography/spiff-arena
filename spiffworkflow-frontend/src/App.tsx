import { defineAbility } from '@casl/ability';
import React from 'react';

import { createBrowserRouter, Outlet, RouterProvider } from 'react-router-dom';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AbilityContext } from './contexts/Can';
import APIErrorProvider from './contexts/APIErrorContext';
import ContainerForExtensions from './ContainerForExtensions';
import PublicRoutes from './routes/PublicRoutes';

const queryClient = new QueryClient();

export default function App() {
  const ability = defineAbility(() => {});
  const routeComponents = () => {
    return [
      { path: 'public/*', element: <PublicRoutes /> },
      {
        path: '*',
        element: <ContainerForExtensions />,
      },
    ];
  };

  const layout = () => {
    return (
      <QueryClientProvider client={queryClient}>
        <div className="cds--white">
          <APIErrorProvider>
            <AbilityContext.Provider value={ability}>
              <Outlet />
            </AbilityContext.Provider>
          </APIErrorProvider>
        </div>
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
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
