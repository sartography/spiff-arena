import { act, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MessageEditor } from './MessageEditor';

const { makeCallToBackend } = vi.hoisted(() => {
  return {
    makeCallToBackend: vi.fn(),
  };
});

let latestCustomFormProps: any = null;

vi.mock('../../services/HttpService', () => {
  return {
    default: {
      makeCallToBackend,
    },
  };
});

vi.mock('../../helpers', () => {
  return {
    modifyProcessIdentifierForPathParam: (identifier: string) =>
      identifier.replace(/\//g, ':'),
    setPageTitle: vi.fn(),
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

vi.mock('../CustomForm', () => {
  return {
    default: (props: any) => {
      const { formData, schema } = props;
      latestCustomFormProps = props;
      const selectedValue = formData.useExistingSharedMessageId;
      const selectedOption =
        schema.properties.useExistingSharedMessageId.oneOf.find(
          (option: any) => option.const === selectedValue,
        );
      return (
        <>
          <div data-testid="selected-shared-message">
            {selectedOption?.title || selectedValue}
          </div>
          <button
            data-testid="choose-parent-location"
            onClick={() =>
              latestCustomFormProps.onChange({
                formData: {
                  ...formData,
                  processGroupIdentifier: 'order',
                  useExistingSharedMessageId: 'none',
                },
              })
            }
            type="button"
          >
            move to parent location
          </button>
          <button
            data-testid="choose-parent-message"
            onClick={() =>
              latestCustomFormProps.onChange({
                formData: {
                  ...formData,
                  useExistingSharedMessageId: '1441',
                },
              })
            }
            type="button"
          >
            choose parent
          </button>
          <button
            data-testid="customize-selected-message"
            onClick={() =>
              latestCustomFormProps.onChange({
                formData: {
                  ...latestCustomFormProps.formData,
                  schema: '{"type":"object"}',
                },
              })
            }
            type="button"
          >
            customize selected message
          </button>
          <button
            data-testid="save-message"
            onClick={() =>
              latestCustomFormProps.onSubmit({
                formData: latestCustomFormProps.formData,
              })
            }
            type="button"
          >
            save
          </button>
        </>
      );
    },
  };
});

describe('MessageEditor', () => {
  beforeEach(() => {
    makeCallToBackend.mockReset();
    latestCustomFormProps = null;
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
      'request-for-information-received (order)',
    );
  });

  it('removes the local message definition when selecting an ancestor shared message', async () => {
    render(
      <MessageEditor
        modifiedProcessGroupIdentifier="order/survey"
        messageId="request-for-information-received"
        messageEvent={{ eventBus: { fire: vi.fn() } }}
        correlationProperties={[]}
        elementId="Task_1"
      />,
    );

    const processGroupCall = makeCallToBackend.mock.calls
      .map((call) => call[0])
      .find((call) => call.path === '/process-groups/order/survey');
    const messageModelsCall = makeCallToBackend.mock.calls
      .map((call) => call[0])
      .find((call) => call.path === '/message-models/order/survey');

    await act(async () => {
      processGroupCall.successCallback({
        display_name: 'Survey',
        messages: {
          'request-for-information-received': {
            correlation_properties: {
              survey_id: { retrieval_expression: 'survey_id' },
            },
            schema: {},
          },
        },
      });
    });

    await act(async () => {
      messageModelsCall.successCallback({
        messages: [
          {
            id: 1441,
            identifier: 'request-for-information-received',
            location: 'order',
            schema: {},
            correlation_properties: [],
          },
          {
            id: 1442,
            identifier: 'request-for-information-received',
            location: 'order/survey',
            schema: {},
            correlation_properties: [],
          },
        ],
      });
    });

    expect(screen.getByTestId('selected-shared-message')).toHaveTextContent(
      'request-for-information-received (order/survey)',
    );

    await act(async () => {
      screen.getByTestId('choose-parent-message').click();
    });

    expect(screen.getByTestId('selected-shared-message')).toHaveTextContent(
      'request-for-information-received (order)',
    );

    await act(async () => {
      screen.getByTestId('save-message').click();
    });

    const updateCall = makeCallToBackend.mock.calls
      .map((call) => call[0])
      .find(
        (call) =>
          call.path === '/process-groups/order:survey' &&
          call.httpMethod === 'PUT',
      );

    expect(updateCall).toBeTruthy();
    expect(updateCall.postBody.messages).toEqual({});
  });

  it('does not show the unsynced warning for an inherited ancestor message', async () => {
    render(
      <MessageEditor
        modifiedProcessGroupIdentifier="order/survey"
        messageId="request-for-information-received"
        messageEvent={{ eventBus: { fire: vi.fn() } }}
        correlationProperties={[
          {
            id: 'survey_id',
            retrievalExpression: 'survey_id',
          },
        ]}
        elementId="Task_1"
      />,
    );

    const processGroupCall = makeCallToBackend.mock.calls
      .map((call) => call[0])
      .find((call) => call.path === '/process-groups/order/survey');
    const messageModelsCall = makeCallToBackend.mock.calls
      .map((call) => call[0])
      .find((call) => call.path === '/message-models/order/survey');

    await act(async () => {
      processGroupCall.successCallback({
        display_name: 'Survey',
        messages: {},
      });
    });

    await act(async () => {
      messageModelsCall.successCallback({
        messages: [
          {
            id: 1441,
            identifier: 'request-for-information-received',
            location: 'order',
            schema: {},
            correlation_properties: [
              {
                identifier: 'survey_id',
                retrieval_expression: 'survey_id',
              },
            ],
          },
        ],
      });
    });

    expect(screen.queryByText('save_warning_message')).not.toBeInTheDocument();
  });

  it('updates the target process group when moving a message to a new location', async () => {
    render(
      <MessageEditor
        modifiedProcessGroupIdentifier="order/survey"
        messageId="request-for-information-received"
        messageEvent={{ eventBus: { fire: vi.fn() } }}
        correlationProperties={[]}
        elementId="Task_1"
      />,
    );

    const processGroupCall = makeCallToBackend.mock.calls
      .map((call) => call[0])
      .find((call) => call.path === '/process-groups/order/survey');
    const messageModelsCall = makeCallToBackend.mock.calls
      .map((call) => call[0])
      .find((call) => call.path === '/message-models/order/survey');

    await act(async () => {
      processGroupCall.successCallback({
        display_name: 'Survey',
        messages: {
          'request-for-information-received': {
            id: 1442,
            location: 'order/survey',
            correlation_properties: {
              survey_id: { retrieval_expression: 'survey_id' },
            },
            schema: {},
          },
        },
      });
    });

    await act(async () => {
      messageModelsCall.successCallback({
        messages: [
          {
            id: 1442,
            identifier: 'request-for-information-received',
            location: 'order/survey',
            schema: {},
            correlation_properties: [],
          },
        ],
      });
    });

    await act(async () => {
      screen.getByTestId('choose-parent-location').click();
    });

    await act(async () => {
      screen.getByTestId('save-message').click();
    });

    const targetProcessGroupGetCall = makeCallToBackend.mock.calls
      .map((call) => call[0])
      .find((call) => call.path === '/process-groups/order');

    expect(targetProcessGroupGetCall).toBeTruthy();

    await act(async () => {
      targetProcessGroupGetCall.successCallback({
        display_name: 'Order',
        messages: {},
      });
    });

    const sourceUpdateCall = makeCallToBackend.mock.calls
      .map((call) => call[0])
      .find(
        (call) =>
          call.path === '/process-groups/order:survey' &&
          call.httpMethod === 'PUT',
      );

    expect(sourceUpdateCall).toBeTruthy();
    expect(sourceUpdateCall.postBody.messages).toEqual({});

    await act(async () => {
      sourceUpdateCall.successCallback({
        display_name: 'Survey',
        messages: {},
      });
    });

    const completedTargetUpdateCall = makeCallToBackend.mock.calls
      .map((call) => call[0])
      .find(
        (call) =>
          call.path === '/process-groups/order' && call.httpMethod === 'PUT',
      );

    expect(completedTargetUpdateCall).toBeTruthy();
    expect(completedTargetUpdateCall.postBody.messages).toEqual({
      'request-for-information-received': {
        correlation_properties: {
          survey_id: { retrieval_expression: 'survey_id' },
        },
        schema: {},
        id: 1442,
        location: 'order',
      },
    });
  });

  it('creates a local override when an inherited ancestor message is customized', async () => {
    render(
      <MessageEditor
        modifiedProcessGroupIdentifier="order/request-for-information"
        messageId="request-for-information-received"
        messageEvent={{ eventBus: { fire: vi.fn() } }}
        correlationProperties={[]}
        elementId="Task_1"
      />,
    );

    const processGroupCall = makeCallToBackend.mock.calls
      .map((call) => call[0])
      .find(
        (call) => call.path === '/process-groups/order/request-for-information',
      );
    const messageModelsCall = makeCallToBackend.mock.calls
      .map((call) => call[0])
      .find(
        (call) => call.path === '/message-models/order/request-for-information',
      );

    await act(async () => {
      processGroupCall.successCallback({
        display_name: 'Request For Information',
        messages: {},
      });
    });

    await act(async () => {
      messageModelsCall.successCallback({
        messages: [
          {
            id: 1441,
            identifier: 'request-for-information-received',
            location: 'order',
            schema: {},
            correlation_properties: [
              {
                identifier: 'order_uuid',
                retrieval_expression: 'uuid',
              },
            ],
          },
        ],
      });
    });

    expect(screen.getByTestId('selected-shared-message')).toHaveTextContent(
      'request-for-information-received (order)',
    );

    await act(async () => {
      screen.getByTestId('customize-selected-message').click();
    });

    expect(screen.getByTestId('selected-shared-message')).toHaveTextContent(
      'do_not_use_existing_shared_message',
    );

    await act(async () => {
      screen.getByTestId('save-message').click();
    });

    const updateCall = makeCallToBackend.mock.calls
      .map((call) => call[0])
      .find(
        (call) =>
          call.path === '/process-groups/order:request-for-information' &&
          call.httpMethod === 'PUT',
      );

    expect(updateCall).toBeTruthy();
    expect(updateCall.postBody.messages).toEqual({
      'request-for-information-received': {
        correlation_properties: {
          order_uuid: { retrieval_expression: 'uuid' },
        },
        schema: { type: 'object' },
      },
    });
  });
});
