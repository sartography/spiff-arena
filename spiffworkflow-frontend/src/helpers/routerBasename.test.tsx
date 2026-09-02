import { render, screen } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { getRouterBasename } from './basePath';

const routes = [
  { path: '/', element: <div>home</div> },
  { path: '/tasks', element: <div>tasks</div> },
];

describe('router basename', () => {
  it('routes at the site root by default', () => {
    const router = createMemoryRouter(routes, { initialEntries: ['/'] });

    render(<RouterProvider router={router} />);

    expect(screen.getByText('home')).toBeInTheDocument();
  });

  it('supports a direct deep link beneath /workflow/', () => {
    const router = createMemoryRouter(routes, {
      basename: getRouterBasename('/workflow/'),
      initialEntries: ['/workflow/tasks'],
    });

    render(<RouterProvider router={router} />);

    expect(screen.getByText('tasks')).toBeInTheDocument();
  });
});
