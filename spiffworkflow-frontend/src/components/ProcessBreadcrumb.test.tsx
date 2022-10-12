import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import ProcessBreadcrumb from './ProcessBreadcrumb';

test('renders home link', () => {
  render(
    <BrowserRouter>
      <ProcessBreadcrumb />
    </BrowserRouter>
  );
  const homeElement = screen.getByText(/Process Groups/);
  expect(homeElement).toBeInTheDocument();
});

test('renders hotCrumbs', () => {
  render(
    <BrowserRouter>
      <ProcessBreadcrumb
        hotCrumbs={[['Process Groups', '/admin'], [`Process Group: hey`]]}
      />
    </BrowserRouter>
  );
  const homeElement = screen.getByText(/Process Groups/);
  expect(homeElement).toBeInTheDocument();
  const nextElement = screen.getByText(/Process Group: hey/);
  expect(nextElement).toBeInTheDocument();
});

test('renders process group when given processGroupId', async () => {
  render(
    <BrowserRouter>
      <ProcessBreadcrumb processGroupId="group-a" />
    </BrowserRouter>
  );
  const processGroupElement = screen.getByText(/group-a/);
  expect(processGroupElement).toBeInTheDocument();
  const processGroupBreadcrumbs = await screen.findAllByText(
    /Process Group: group-a/
  );
  expect(processGroupBreadcrumbs[0]).toHaveClass('breadcrumb-item active');
});

test('renders process model when given processModelId', async () => {
  render(
    <BrowserRouter>
      <ProcessBreadcrumb processGroupId="group-b" processModelId="model-c" />
    </BrowserRouter>
  );
  const processGroupElement = screen.getByText(/group-b/);
  expect(processGroupElement).toBeInTheDocument();
  const processModelBreadcrumbs = await screen.findAllByText(
    /Process Model: model-c/
  );
  expect(processModelBreadcrumbs[0]).toHaveClass('breadcrumb-item active');
  const processGroupBreadcrumbs = await screen.findAllByText(
    /Process Group: group-b/
  );
  expect(processGroupBreadcrumbs[0]).toBeInTheDocument();
});
