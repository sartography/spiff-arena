import React from 'react';
import { defineAbility } from '@casl/ability';

import { createBrowserRouter, Outlet, RouterProvider } from 'react-router-dom';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AbilityContext } from './contexts/Can';
import APIErrorProvider from './contexts/APIErrorContext';
import { WidgetRegistryProvider } from './rjsf/registry/WidgetRegistry';
import { initializeWidgets } from './rjsf/registry/initializeWidgets';
import ContainerForExtensions from './ContainerForExtensions';
import PublicRoutes from './views/PublicRoutes';

const queryClient = new QueryClient();

export default function App() {
  const ability = defineAbility(() => {});
  
  // Initialize the widget system when the app loads
  React.useEffect(() => {
    // Initialize widgets on component mount
    initializeWidgets().catch((error) => {
      console.error('Failed to initialize widget system:', error);
    });
  }, []);
  
  const routeComponents = () => {
    return [
      { path: 'public/*', element: <PublicRoutes /> },
      {
        path: '*',
        element: <ContainerForExtensions />,
      },
    ];
  };

  /**
   * Note that QueryClientProvider and ReactQueryDevTools
   * are React Query, now branded under the Tanstack packages.
   * https://tanstack.com/query/latest
   */
  const layout = () => {
    return (
      <div className="cds--white">
        <QueryClientProvider client={queryClient}>
          <APIErrorProvider>
            <AbilityContext.Provider value={ability}>
              <WidgetRegistryProvider>
                <Outlet />
                <ReactQueryDevtools initialIsOpen={false} />
              </WidgetRegistryProvider>
            </AbilityContext.Provider>
          </APIErrorProvider>
        </QueryClientProvider>
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
