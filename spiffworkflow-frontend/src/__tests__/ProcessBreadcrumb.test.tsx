import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';

test('renders no breadcrumbs when hotCrumbs are omitted', () => {
  const { container } = render(
    <BrowserRouter>
      <ProcessBreadcrumb />
    </BrowserRouter>,
  );
  expect(container).toBeEmptyDOMElement();
});

test('renders hotCrumbs', () => {
  render(
    <BrowserRouter>
      <ProcessBreadcrumb
        hotCrumbs={[
          ['Process Groups', '/process-groups'],
          [`Process Group: hey`],
        ]}
      />
    </BrowserRouter>,
  );
  const homeElement = screen.getByText(/Process Groups/);
  expect(homeElement).toBeInTheDocument();
  const nextElement = screen.getByText(/Process Group: hey/);
  expect(nextElement).toBeInTheDocument();
});
