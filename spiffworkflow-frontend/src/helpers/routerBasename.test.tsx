import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { getRouterBasename } from './basePath';

describe('router basename integration', () => {
  const makeRouter = (
    basename: string | undefined,
    initialEntries: string[],
  ) => {
    return createMemoryRouter(
      [
        { path: '/', element: <div>home</div> },
        { path: '/about', element: <div>about</div> },
        { path: '/tasks', element: <div>tasks</div> },
      ],
      { basename, initialEntries },
    );
  };

  it('renders at root when basename is undefined (default /)', () => {
    const basename = getRouterBasename('/');
    expect(basename).toBeUndefined();
    const router = makeRouter(basename, ['/']);
    render(<RouterProvider router={router} />);
    expect(screen.getByText('home')).toBeInTheDocument();
  });

  it('renders at root via /workflow/ when basename is /workflow', () => {
    const basename = getRouterBasename('/workflow/');
    expect(basename).toEqual('/workflow');
    const router = makeRouter(basename, ['/workflow/']);
    render(<RouterProvider router={router} />);
    expect(screen.getByText('home')).toBeInTheDocument();
  });

  it('routes to /workflow/about under workflow basename', () => {
    const basename = getRouterBasename('/workflow/');
    const router = makeRouter(basename, ['/workflow/about']);
    render(<RouterProvider router={router} />);
    expect(screen.getByText('about')).toBeInTheDocument();
  });

  it('supports deep link navigation under workflow basename', () => {
    const basename = getRouterBasename('/workflow/');
    const router = makeRouter(basename, ['/workflow/tasks']);
    render(<RouterProvider router={router} />);
    expect(screen.getByText('tasks')).toBeInTheDocument();
  });

  it('asset base and router basename stay in sync', () => {
    const baseUrl = '/workflow/';
    const basename = getRouterBasename(baseUrl);
    // asset base would be /workflow/ for Vite, router basename /workflow
    expect(baseUrl).toEqual('/workflow/');
    expect(basename).toEqual('/workflow');
    // A build asset URL and a router URL share the same prefix
    expect(`${baseUrl}assets/app.js`).toEqual('/workflow/assets/app.js');
    expect(`${basename}/about`).toEqual('/workflow/about');
  });
});
