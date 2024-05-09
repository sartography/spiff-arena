import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import ProcessBreadcrumb from './ProcessBreadcrumb';

test('renders home link', () => {
  // render(
  //   <BrowserRouter>
  //     <ProcessBreadcrumb />
  //   </BrowserRouter>
  // );
  // const homeElement = screen.getByText(/Grupos de Processo/);
  // expect(homeElement).toBeInTheDocument();
});

test('renders hotCrumbs', () => {
  render(
    <BrowserRouter>
      <ProcessBreadcrumb
        hotCrumbs={[
          ['Grupos de Processo', '/process-groups'],
          [`Grupo de Processo: hey`],
        ]}
      />
    </BrowserRouter>
  );
  const homeElement = screen.getByText(/Grupos de Processo/);
  expect(homeElement).toBeInTheDocument();
  const nextElement = screen.getByText(/Grupo de Processo: hey/);
  expect(nextElement).toBeInTheDocument();
});
