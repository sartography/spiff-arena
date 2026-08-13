import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import TreePanel from './TreePanel';

describe('TreePanel', () => {
  it('does not render the process-group count for an empty tree', () => {
    render(<TreePanel processGroups={[]} />);

    expect(screen.getByRole('tree')).toBeEmptyDOMElement();
  });

  it('renders available process groups', () => {
    render(
      <TreePanel
        processGroups={[
          {
            id: 'invoice-approval',
            display_name: 'Invoice Approval',
            process_groups: [],
            process_models: [],
          },
        ]}
      />,
    );

    expect(screen.getByText('Invoice Approval')).toBeVisible();
  });
});
