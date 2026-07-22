import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Notification } from './Notification';

describe('Notification', () => {
  it('only intercepts pointer events on the visible alert', () => {
    render(
      <Notification title="Saved" data-testid="notification">
        Changes were saved.
      </Notification>,
    );

    expect(screen.getByTestId('notification')).toHaveStyle({
      pointerEvents: 'none',
    });
    expect(screen.getByRole('alert')).toHaveStyle({ pointerEvents: 'auto' });
  });
});
