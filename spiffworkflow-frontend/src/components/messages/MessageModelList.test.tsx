import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import MessageModelList from './MessageModelList';

const { makeCallToBackend, messageEditorMock } = vi.hoisted(() => {
  return {
    makeCallToBackend: vi.fn(),
    messageEditorMock: vi.fn(),
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

vi.mock('./MessageEditor', () => {
  return {
    MessageEditor: (props: any) => {
      messageEditorMock(props);
      return (
        <div
          data-testid="message-editor"
          data-hide-submit-button={String(props.hideSubmitButton)}
          data-message-id={props.messageId}
          data-location={props.modifiedProcessGroupIdentifier}
        >
          message editor
        </div>
      );
    },
  };
});

describe('MessageModelList', () => {
  beforeEach(() => {
    makeCallToBackend.mockReset();
    messageEditorMock.mockReset();
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
    expect(screen.getByTestId('message-editor')).toHaveAttribute(
      'data-hide-submit-button',
      'true',
    );
  });

  it('provides an explicit close action for the message editor dialog', async () => {
    render(
      <MemoryRouter>
        <MessageModelList />
      </MemoryRouter>,
    );

    const listCall = makeCallToBackend.mock.calls
      .map((call) => call[0])
      .find((call) => call.path === '/all-message-models');

    await act(async () => {
      listCall.successCallback({
        messages: [
          {
            id: 1442,
            identifier: 'request-for-information-received',
            location: 'order',
            schema: {},
            correlation_properties: [],
            process_model_identifiers: [],
          },
        ],
      });
    });

    fireEvent.click(screen.getByRole('button', { name: 'edit' }));

    expect(screen.getByTestId('message-editor')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'close' }));

    expect(screen.queryByTestId('message-editor')).not.toBeInTheDocument();
  });

  it('opens a blank message editor after validating the chosen create location', async () => {
    render(
      <MemoryRouter>
        <MessageModelList />
      </MemoryRouter>,
    );

    const listCall = makeCallToBackend.mock.calls
      .map((call) => call[0])
      .find((call) => call.path === '/all-message-models');

    await act(async () => {
      listCall.successCallback({ messages: [] });
    });

    fireEvent.click(screen.getByRole('button', { name: 'add_message_model' }));

    fireEvent.change(screen.getByRole('textbox', { name: 'location' }), {
      target: { value: 'order/request-for-information' },
    });

    fireEvent.click(screen.getByRole('button', { name: 'continue' }));

    const processGroupCall = makeCallToBackend.mock.calls
      .map((call) => call[0])
      .find(
        (call) => call.path === '/process-groups/order:request-for-information',
      );

    expect(processGroupCall).toBeTruthy();

    await act(async () => {
      processGroupCall.successCallback({
        id: 'order/request-for-information',
        display_name: 'Request For Information',
        messages: {},
      });
    });

    expect(screen.getByTestId('message-editor')).toHaveAttribute(
      'data-message-id',
      '',
    );
    expect(screen.getByTestId('message-editor')).toHaveAttribute(
      'data-location',
      'order:request-for-information',
    );
  });

  it('deletes a message model after confirmation', async () => {
    render(
      <MemoryRouter>
        <MessageModelList />
      </MemoryRouter>,
    );

    const listCall = makeCallToBackend.mock.calls
      .map((call) => call[0])
      .find((call) => call.path === '/all-message-models');

    await act(async () => {
      listCall.successCallback({
        messages: [
          {
            id: 1442,
            identifier: 'request-for-information-received',
            location: 'order',
            schema: {},
            correlation_properties: [],
            process_model_identifiers: ['order/request-for-information/model'],
          },
          {
            id: 1443,
            identifier: 'keep-me',
            location: 'order',
            schema: {},
            correlation_properties: [],
            process_model_identifiers: [],
          },
        ],
      });
    });

    fireEvent.click(screen.getAllByRole('button', { name: 'delete' })[0]);

    expect(
      screen.getByText('delete_message_model_confirmation'),
    ).toBeInTheDocument();

    fireEvent.click(
      within(screen.getByRole('dialog')).getByRole('button', {
        name: 'delete',
      }),
    );

    const processGroupCall = makeCallToBackend.mock.calls
      .map((call) => call[0])
      .find((call) => call.path === '/process-groups/order');

    expect(processGroupCall).toBeTruthy();

    await act(async () => {
      processGroupCall.successCallback({
        id: 'order',
        display_name: 'Order',
        messages: {
          'request-for-information-received': {
            schema: {},
          },
          'keep-me': {
            schema: {},
          },
        },
      });
    });

    const updateCall = makeCallToBackend.mock.calls
      .map((call) => call[0])
      .find(
        (call) =>
          call.path === '/process-groups/order' && call.httpMethod === 'PUT',
      );

    expect(updateCall).toBeTruthy();
    expect(updateCall.postBody.messages).toEqual({
      'keep-me': {
        schema: {},
      },
    });
  });
});
