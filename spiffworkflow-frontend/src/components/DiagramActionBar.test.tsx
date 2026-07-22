import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import DiagramActionBar from '../../packages/bpmn-js-spiffworkflow-react/src/components/DiagramActionBar';

// The "Last saved" indicator (issue #1642) is passed into the action bar as a
// ready-to-render node via the lastSavedElement slot.
describe('DiagramActionBar lastSavedElement', () => {
  const requiredProps = {
    saveLabel: 'Save',
    setPrimaryLabel: 'Set as primary file',
  };

  it('renders the last saved element when provided', () => {
    render(
      <DiagramActionBar
        {...requiredProps}
        lastSavedElement={<span>Last saved: 2026-07-21 14:03:00</span>}
      />,
    );
    expect(
      screen.getByText('Last saved: 2026-07-21 14:03:00'),
    ).toBeInTheDocument();
  });

  it('renders the last saved element before the save button', () => {
    render(
      <DiagramActionBar
        {...requiredProps}
        canSave
        onSave={() => {}}
        lastSavedElement={<span>Last saved: 2026-07-21 14:03:00</span>}
      />,
    );

    const lastSavedElement = screen.getByText(
      'Last saved: 2026-07-21 14:03:00',
    );
    const saveButton = screen.getByRole('button', { name: 'Save' });
    const actionBarChildren = Array.from(
      lastSavedElement.parentElement?.children || [],
    );

    expect(actionBarChildren.indexOf(lastSavedElement)).toBeLessThan(
      actionBarChildren.indexOf(saveButton),
    );
  });

  it('renders nothing for the indicator when no last saved element is given', () => {
    render(<DiagramActionBar {...requiredProps} />);
    expect(screen.queryByText(/Last saved:/)).not.toBeInTheDocument();
  });
});
