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
    default: (props: any) => {
      const { formData, schema } = props;
      latestCustomFormProps = props;
      const selectedValue = formData.useExistingSharedMessageId;
      const selectedOption = schema.properties.useExistingSharedMessageId.oneOf.find(
        (option: any) => option.const === selectedValue,
      );
      return (
        <>
          <div data-testid="selected-shared-message">
            {selectedOption?.title || selectedValue}
          </div>
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
          call.path === '/process-groups/order/survey' &&
          call.httpMethod === 'PUT',
      );

    expect(updateCall).toBeTruthy();
    expect(updateCall.postBody.messages).toEqual({});
  });
});
