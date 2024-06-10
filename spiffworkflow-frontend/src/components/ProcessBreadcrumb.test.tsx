import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import ProcessBreadcrumb from './ProcessBreadcrumb';

test('renders home link', () => {
  // render(
  //   <BrowserRouter>
  //     <ProcessBreadcrumb />
  //   </BrowserRouter>
  // );
  // const homeElement = screen.getByText(/Process Groups/);
  // expect(homeElement).toBeInTheDocument();
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
