import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import MessageListPage from './MessageListPage';

vi.mock('../components/messages/MessageInstanceList', () => {
  return {
    default: () => <div>message instances</div>,
  };
});

vi.mock('../components/messages/MessageModelList', () => {
  return {
    default: () => <div>message models</div>,
  };
});

vi.mock('../helpers', () => {
  return {
    setPageTitle: vi.fn(),
  };
});

vi.mock('react-i18next', () => {
  return {
    useTranslation: () => ({
      t: (value: string) => value,
    }),
  };
});

describe('MessageListPage', () => {
  it('shows the message model management tab', () => {
    render(
      <MemoryRouter>
        <MessageListPage />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole('tab', { name: 'Message Models' }));

    expect(screen.getByText('message models')).toBeInTheDocument();
  });
});
