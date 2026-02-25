import { act, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MessageEditor } from './MessageEditor';

const { makeCallToBackend } = vi.hoisted(() => {
  return {
    makeCallToBackend: vi.fn(),
  };
});

vi.mock('../../services/HttpService', () => {
  return {
    default: {
      makeCallToBackend,
    },
  };
});

vi.mock('../../helpers', () => {
  return {
    setPageTitle: vi.fn(),
    unModifyProcessIdentifierForPathParam: (identifier: string) => identifier,
  };
});

vi.mock('react-i18next', () => {
  return {
    useTranslation: () => ({
      t: (value: string) => value,
    }),
  };
});

vi.mock('../CustomForm', () => {
  return {
    default: ({ formData }: any) => (
      <div data-testid="selected-shared-message">
        {formData.useExistingSharedMessageId}
      </div>
    ),
  };
});

describe('MessageEditor', () => {
  beforeEach(() => {
    makeCallToBackend.mockReset();
  });

  it('waits for message models before initializing form state', async () => {
    render(
      <MessageEditor
        modifiedProcessGroupIdentifier="order/residential"
        messageId="request-for-information-received"
        messageEvent={{ eventBus: { fire: vi.fn() } }}
        correlationProperties={[]}
        elementId="Task_1"
      />,
    );

    const processGroupCall = makeCallToBackend.mock.calls
      .map((call) => call[0])
      .find((call) => call.path === '/process-groups/order/residential');
    const messageModelsCall = makeCallToBackend.mock.calls
      .map((call) => call[0])
      .find((call) => call.path === '/message-models/order/residential');

    expect(processGroupCall).toBeTruthy();
    expect(messageModelsCall).toBeTruthy();

    await act(async () => {
      processGroupCall.successCallback({
        display_name: 'Residential',
        messages: {},
      });
    });

    expect(
      screen.queryByTestId('selected-shared-message'),
    ).not.toBeInTheDocument();

    await act(async () => {
      messageModelsCall.successCallback({
        messages: [
          {
            id: 1440,
            identifier: 'document-uploaded',
            location: 'order',
            schema: {},
            correlation_properties: [],
          },
          {
            id: 1441,
            identifier: 'request-for-information-received',
            location: 'order',
            schema: {},
            correlation_properties: [],
          },
        ],
      });
    });

    expect(screen.getByTestId('selected-shared-message')).toHaveTextContent(
      '1441',
    );
  });
});
