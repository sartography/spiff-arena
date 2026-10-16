import { act, renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import useDiagramMessageEditor, {
  MESSAGE_EDITOR_REQUEST_PARAM,
  MESSAGE_MODEL_SAVED,
  notifyMessageEditorSaved,
} from './useDiagramMessageEditor';

const { makeCallToBackend } = vi.hoisted(() => ({
  makeCallToBackend: vi.fn(),
}));
vi.mock('../services/HttpService', () => ({ default: { makeCallToBackend } }));

function bus() {
  const listeners = new Map<string, Set<(event?: any) => void>>();
  return {
    fire: vi.fn((name: string, event?: any) =>
      listeners.get(name)?.forEach((fn) => fn(event)),
    ),
    on: (name: string, fn: (event?: any) => void) => {
      if (!listeners.has(name)) listeners.set(name, new Set());
      listeners.get(name)!.add(fn);
    },
    off: (name: string, fn: (event?: any) => void) =>
      listeners.get(name)?.delete(fn),
  };
}
const options = {
  diagramKey: 'restaurant/waiter/waiter.bpmn',
  sourceLocation: 'restaurant/waiter',
  messagesHref: '/arena/messages',
  messageListPath: '/message-models/restaurant:waiter',
  canAccessMessages: true,
};
const saved = {
  identifier: 'reply',
  location: 'restaurant',
  correlation_properties: [],
};

function setup(messageId?: string) {
  const popup = { closed: false } as Window;
  const open = vi.spyOn(window, 'open').mockReturnValue(popup);
  const eventBus = bus();
  const element = { businessObject: { messageRef: undefined as any } };
  const applyMessage = vi.fn();
  const event = {
    eventBus,
    element,
    applyMessage,
    value: { elementId: 'Receiver', messageId },
  };
  const hook = renderHook((props) => useDiagramMessageEditor(props), {
    initialProps: options,
  });
  act(() => hook.result.current.onLaunchMessageEditor(event));
  const url = new URL(
    String(open.mock.calls.at(-1)![0]),
    window.location.origin,
  );
  const requestId = url.searchParams.get(MESSAGE_EDITOR_REQUEST_PARAM);
  const notify = (
    overrides = {},
    origin = window.location.origin,
    source: any = popup,
  ) => {
    window.dispatchEvent(
      new MessageEvent('message', {
        origin,
        source,
        data: {
          type: MESSAGE_MODEL_SAVED,
          requestId,
          messageId: 'reply',
          location: 'restaurant',
          ...overrides,
        },
      }),
    );
  };
  return { hook, event, eventBus, element, applyMessage, url, notify };
}

function respond(messages = [saved]) {
  makeCallToBackend.mock.calls.at(-1)![0].successCallback({ messages });
}

describe('diagram message editor lifecycle', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    makeCallToBackend.mockReset();
  });

  it('refreshes the scoped dropdown on return without changing XML', async () => {
    const eventBus = bus();
    const hook = renderHook(() => useDiagramMessageEditor(options));
    act(() => hook.result.current.onMessagesRequested({ eventBus }));
    await act(async () => respond());
    expect(makeCallToBackend.mock.calls[0][0].path).toBe(
      options.messageListPath,
    );
    expect(eventBus.fire).toHaveBeenCalledWith('spiff.messages.returned', {
      configuration: { messages: [saved] },
    });
    act(() => window.dispatchEvent(new Event('focus')));
    await act(async () => respond());
    act(() => document.dispatchEvent(new Event('visibilitychange')));
    await act(async () => respond());
    expect(makeCallToBackend).toHaveBeenCalledTimes(3);
    expect(
      eventBus.fire.mock.calls.every(
        ([name]) => name === 'spiff.messages.returned',
      ),
    ).toBe(true);
    hook.unmount();
    window.dispatchEvent(new Event('focus'));
    expect(makeCallToBackend).toHaveBeenCalledTimes(3);
  });

  it('selects the created message on the original element once, using fetched catalog data', async () => {
    const { url, notify, applyMessage } = setup();
    expect(url.pathname).toBe('/arena/messages');
    expect(url.searchParams.get('source_location')).toBe('restaurant/waiter');
    expect(url.searchParams.has('message_id')).toBe(false);
    act(() => notify());
    await act(async () => respond());
    expect(applyMessage).toHaveBeenCalledExactlyOnceWith(saved);
    act(() => notify());
    await act(async () => respond());
    expect(applyMessage).toHaveBeenCalledTimes(1);
  });

  it.each(['changed', 'removed', 'existing'])(
    'does not autoassign when the target is %s',
    async (reason) => {
      const { event, element, eventBus, notify, applyMessage } = setup(
        reason === 'existing' ? 'old' : undefined,
      );
      if (reason === 'changed') {
        element.businessObject.messageRef = { id: 'other' };
        eventBus.fire('commandStack.changed');
        element.businessObject.messageRef = undefined; // even changing back should not overwrite the user's choice
      } else if (reason === 'removed') {
        eventBus.fire('shape.removed', { element: event.element });
      }
      act(() => notify());
      await act(async () => respond());
      expect(applyMessage).not.toHaveBeenCalled();
    },
  );

  it('ignores foreign origins, unrelated windows, and unknown request IDs', () => {
    const { notify, applyMessage } = setup();
    act(() => {
      notify({}, 'https://unrelated.example');
      notify({}, window.location.origin, {});
      notify({ requestId: 'unknown' });
    });
    expect(makeCallToBackend).not.toHaveBeenCalled();
    expect(applyMessage).not.toHaveBeenCalled();
  });

  it('does not select an out-of-scope or shadowed message', async () => {
    const { notify, applyMessage } = setup();
    act(() => notify({ location: 'elsewhere' }));
    await act(async () => respond());
    act(() => notify());
    await act(async () =>
      respond([saved, { ...saved, location: 'restaurant/waiter' }]),
    );
    expect(applyMessage).not.toHaveBeenCalled();
  });

  it('ignores an outstanding response after navigating away', async () => {
    const { hook, notify, applyMessage, eventBus } = setup();
    act(() => notify());
    hook.rerender({ ...options, diagramKey: 'another.bpmn' });
    await act(async () => respond());
    expect(eventBus.fire).not.toHaveBeenCalled();
    expect(applyMessage).not.toHaveBeenCalled();
  });

  it('does not alter the diagram if refreshing the catalog fails', async () => {
    const { notify, applyMessage } = setup();
    act(() => notify());
    await act(async () =>
      makeCallToBackend.mock.calls
        .at(-1)![0]
        .failureCallback(new Error('offline')),
    );
    expect(applyMessage).not.toHaveBeenCalled();
  });

  it('notifies the opener only with launch context', () => {
    const postMessage = vi.fn();
    vi.stubGlobal('opener', { postMessage, closed: false });
    try {
      notifyMessageEditorSaved(null, 'reply', 'restaurant');
      expect(postMessage).not.toHaveBeenCalled();
      notifyMessageEditorSaved('request', 'reply', 'restaurant');
      expect(postMessage).toHaveBeenCalledWith(
        {
          type: MESSAGE_MODEL_SAVED,
          requestId: 'request',
          messageId: 'reply',
          location: 'restaurant',
        },
        window.location.origin,
      );
    } finally {
      vi.unstubAllGlobals();
    }
  });
});
