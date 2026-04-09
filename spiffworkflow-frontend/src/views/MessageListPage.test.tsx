import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import MessageListPage from './MessageListPage';

const messageModelListMock = vi.fn();

vi.mock('../components/messages/MessageInstanceList', () => {
  return {
    default: () => <div>message instances</div>,
  };
});

vi.mock('../components/messages/MessageModelList', () => {
  return {
    default: (props: any) => {
      messageModelListMock(props);
      return <div>message models</div>;
    },
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

  it('forwards the source location query param to the message model list', () => {
    messageModelListMock.mockReset();

    render(
      <MemoryRouter
        initialEntries={[
          '/messages?message_id=request-for-information-received&source_location=order%2Frequest-for-information%2Frequest-for-information',
        ]}
      >
        <MessageListPage />
      </MemoryRouter>,
    );

    expect(messageModelListMock).toHaveBeenCalledWith(
      expect.objectContaining({
        initialMessageId: 'request-for-information-received',
        initialSourceLocation:
          'order/request-for-information/request-for-information',
      }),
    );
  });
});
