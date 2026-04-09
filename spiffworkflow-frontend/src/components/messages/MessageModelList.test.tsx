import { act, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import MessageModelList from './MessageModelList';

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
    getPageInfoFromSearchParams: () => ({
      page: 1,
      perPage: 50,
    }),
    modifyProcessIdentifierForPathParam: (identifier: string) =>
      identifier.replace(/\//g, ':'),
    unModifyProcessIdentifierForPathParam: (identifier: string) =>
      identifier.replace(/:/g, '/'),
  };
});

vi.mock('react-i18next', () => {
  return {
    useTranslation: () => ({
      t: (value: string) => value,
    }),
  };
});

describe('MessageModelList', () => {
  beforeEach(() => {
    makeCallToBackend.mockReset();
  });

  it('renders message models from the current api response shape', async () => {
    render(
      <MemoryRouter>
        <MessageModelList />
      </MemoryRouter>,
    );

    const listCall = makeCallToBackend.mock.calls
      .map((call) => call[0])
      .find((call) => call.path === '/all-message-models');

    expect(listCall).toBeTruthy();

    await act(async () => {
      listCall.successCallback({
        messages: [
          {
            id: 1442,
            identifier: 'request-for-information-received',
            location: 'order',
            schema: {},
            correlation_properties: [
              {
                identifier: 'survey_id',
                retrieval_expression: 'survey.id',
              },
            ],
          },
        ],
      });
    });

    expect(
      screen.getByText('request-for-information-received'),
    ).toBeInTheDocument();
    expect(screen.getByText('order')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'edit' })).toBeInTheDocument();
  });

  it('opens the nearest matching message model for the provided source location', async () => {
    render(
      <MemoryRouter>
        {/* @ts-expect-error - prop added as part of the new selection flow */}
        <MessageModelList
          initialMessageId="request-for-information-received"
          initialSourceLocation="order/request-for-information/request-for-information"
        />
      </MemoryRouter>,
    );

    const listCall = makeCallToBackend.mock.calls
      .map((call) => call[0])
      .find((call) => call.path === '/all-message-models');

    expect(listCall).toBeTruthy();

    await act(async () => {
      listCall.successCallback({
        messages: [
          {
            id: 1441,
            identifier: 'request-for-information-received',
            location: 'order',
            schema: {},
            correlation_properties: [],
            process_model_identifiers: [],
          },
          {
            id: 1442,
            identifier: 'request-for-information-received',
            location: 'order/request-for-information',
            schema: {},
            correlation_properties: [],
            process_model_identifiers: [],
          },
        ],
      });
    });

    expect(
      screen.getByRole('heading', {
        name: 'request-for-information-received (order/request-for-information)',
      }),
    ).toBeInTheDocument();
  });
});
