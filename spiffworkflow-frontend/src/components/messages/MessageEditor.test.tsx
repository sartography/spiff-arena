import { act, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MessageEditor } from './MessageEditor';

const { makeCallToBackend, setPageTitle } = vi.hoisted(() => {
  return {
    makeCallToBackend: vi.fn(),
    setPageTitle: vi.fn(),
  };
});

let latestCustomFormProps: any = null;
const REQUEST_FOR_INFORMATION_MESSAGE_ID = 'request-for-information-received';

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
    setPageTitle,
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
    setPageTitle.mockReset();
    latestCustomFormProps = null;
  });

  it('waits for message models before initializing form state', async () => {
    render(
      <MessageEditor
        modifiedProcessGroupIdentifier="order/residential"
        messageId={REQUEST_FOR_INFORMATION_MESSAGE_ID}
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
            identifier: REQUEST_FOR_INFORMATION_MESSAGE_ID,
            location: 'order',
            schema: {},
            correlation_properties: [],
          },
        ],
      });
    });

    expect(screen.getByTestId('selected-shared-message')).toHaveTextContent(
      `${REQUEST_FOR_INFORMATION_MESSAGE_ID} (order)`,
    );
    expect(setPageTitle).toHaveBeenCalledWith(['Residential']);
  });

  it('does not overwrite the parent page title when disabled', async () => {
    render(
      <MessageEditor
        modifiedProcessGroupIdentifier="order/residential"
        messageId={REQUEST_FOR_INFORMATION_MESSAGE_ID}
        messageEvent={{ eventBus: { fire: vi.fn() } }}
        correlationProperties={[]}
        elementId="Task_1"
        managePageTitle={false}
      />,
    );

    const processGroupCall = makeCallToBackend.mock.calls
      .map((call) => call[0])
      .find((call) => call.path === '/process-groups/order/residential');
    const messageModelsCall = makeCallToBackend.mock.calls
      .map((call) => call[0])
      .find((call) => call.path === '/message-models/order/residential');

    await act(async () => {
      processGroupCall.successCallback({
        display_name: 'Residential',
        messages: {},
      });
    });

    await act(async () => {
      messageModelsCall.successCallback({
        messages: [],
      });
    });

    expect(setPageTitle).not.toHaveBeenCalled();
  });

  it('removes the local message definition when selecting an ancestor shared message', async () => {
    render(
      <MessageEditor
        modifiedProcessGroupIdentifier="order/survey"
        messageId={REQUEST_FOR_INFORMATION_MESSAGE_ID}
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
          [REQUEST_FOR_INFORMATION_MESSAGE_ID]: {
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
            identifier: REQUEST_FOR_INFORMATION_MESSAGE_ID,
            location: 'order',
            schema: {},
            correlation_properties: [],
          },
          {
            id: 1442,
            identifier: REQUEST_FOR_INFORMATION_MESSAGE_ID,
            location: 'order/survey',
            schema: {},
            correlation_properties: [],
          },
        ],
      });
    });

    expect(screen.getByTestId('selected-shared-message')).toHaveTextContent(
      `${REQUEST_FOR_INFORMATION_MESSAGE_ID} (order/survey)`,
    );

    await act(async () => {
      screen.getByTestId('choose-parent-message').click();
    });

    expect(screen.getByTestId('selected-shared-message')).toHaveTextContent(
      `${REQUEST_FOR_INFORMATION_MESSAGE_ID} (order)`,
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
        messageId={REQUEST_FOR_INFORMATION_MESSAGE_ID}
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
            identifier: REQUEST_FOR_INFORMATION_MESSAGE_ID,
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

  it('moves a message with a single backend request when changing locations', async () => {
    render(
      <MessageEditor
        modifiedProcessGroupIdentifier="order/survey"
        messageId={REQUEST_FOR_INFORMATION_MESSAGE_ID}
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
          [REQUEST_FOR_INFORMATION_MESSAGE_ID]: {
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
            identifier: REQUEST_FOR_INFORMATION_MESSAGE_ID,
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

    const moveCall = makeCallToBackend.mock.calls
      .map((call) => call[0])
      .find(
        (call) =>
          call.path ===
            `/process-groups/order:survey/messages/${REQUEST_FOR_INFORMATION_MESSAGE_ID}/move` &&
          call.httpMethod === 'PUT',
      );

    expect(moveCall).toBeTruthy();
    expect(moveCall.postBody).toEqual({
      target_process_group_identifier: 'order',
      target_message_identifier: REQUEST_FOR_INFORMATION_MESSAGE_ID,
      message_definition: {
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
        messageId={REQUEST_FOR_INFORMATION_MESSAGE_ID}
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
            identifier: REQUEST_FOR_INFORMATION_MESSAGE_ID,
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
      `${REQUEST_FOR_INFORMATION_MESSAGE_ID} (order)`,
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
      [REQUEST_FOR_INFORMATION_MESSAGE_ID]: {
        correlation_properties: {
          order_uuid: { retrieval_expression: 'uuid' },
        },
        schema: { type: 'object' },
      },
    });
  });
});
