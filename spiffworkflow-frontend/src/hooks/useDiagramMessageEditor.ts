import { useCallback, useEffect, useRef } from 'react';
import HttpService from '../services/HttpService';
import { findNearestAncestorLocation } from '../components/messages/MessageHelper';

export const MESSAGE_EDITOR_REQUEST_PARAM = 'message_editor_request';
export const MESSAGE_MODEL_SAVED = 'spiff-arena:message-model-saved';

type CatalogMessage = {
  identifier: string;
  location: string;
  correlation_properties: Array<{
    identifier: string;
    retrieval_expression: string;
  }>;
};

type Launch = {
  popup: Window;
  event: any;
  originalMessage: unknown;
  assign: boolean;
  stopWatching: () => void;
};

const messageRef = (element: any) => {
  const bo = element?.businessObject;
  return bo?.eventDefinitions?.[0]?.messageRef || bo?.messageRef;
};

export function notifyMessageEditorSaved(
  requestId: string | null,
  messageId: string,
  location: string,
) {
  if (requestId && window.opener && !window.opener.closed) {
    window.opener.postMessage(
      { type: MESSAGE_MODEL_SAVED, requestId, messageId, location },
      window.location.origin,
    );
  }
}

export default function useDiagramMessageEditor({
  diagramKey,
  sourceLocation,
  messagesHref,
  messageListPath,
  canAccessMessages,
}: {
  diagramKey: string;
  sourceLocation: string;
  messagesHref: string;
  messageListPath: string;
  canAccessMessages: boolean;
}) {
  const eventBus = useRef<any>(null);
  const launches = useRef(new Map<string, Launch>());
  const generation = useRef(0);
  const refreshSequence = useRef(0);

  const refresh = useCallback(async () => {
    const bus = eventBus.current;
    if (!bus || !canAccessMessages) {
      return null;
    }
    const currentGeneration = generation.current;
    const sequence = ++refreshSequence.current;
    try {
      const result = await new Promise<{ messages: CatalogMessage[] }>(
        (resolve, reject) => {
          HttpService.makeCallToBackend({
            path: messageListPath,
            successCallback: resolve,
            failureCallback: reject,
          });
        },
      );
      if (
        generation.current !== currentGeneration ||
        eventBus.current !== bus
      ) {
        return null;
      }
      // A slow response must not replace a more recently requested catalog.
      if (sequence === refreshSequence.current) {
        bus.fire('spiff.messages.returned', { configuration: result });
      }
      return result.messages || [];
    } catch {
      // Keep the existing dropdown and unsaved diagram intact on request failure.
      return null;
    }
  }, [canAccessMessages, messageListPath]);

  const onMessagesRequested = useCallback(
    (event: any) => {
      eventBus.current = event.eventBus;
      void refresh();
    },
    [refresh],
  );

  const onLaunchMessageEditor = useCallback(
    (event: any) => {
      eventBus.current = event.eventBus;
      const requestId = crypto.randomUUID();
      const params = new URLSearchParams({
        tab: 'models',
        source_location: sourceLocation,
        [MESSAGE_EDITOR_REQUEST_PARAM]: requestId,
      });
      if (event.value?.messageId) {
        params.set('message_id', event.value.messageId);
      }
      const popup = window.open(`${messagesHref}?${params}`, '_blank');
      if (!popup) {
        return;
      }
      for (const [id, launch] of launches.current) {
        if (
          launch.popup.closed ||
          launch.event.value?.elementId === event.value?.elementId
        ) {
          launch.stopWatching();
          launches.current.delete(id);
        }
      }
      const launch: Launch = {
        popup,
        event,
        originalMessage: messageRef(event.element),
        assign:
          !event.value?.messageId && typeof event.applyMessage === 'function',
        stopWatching: () => {},
      };
      const changed = () => {
        if (messageRef(event.element) !== launch.originalMessage) {
          launch.assign = false;
        }
      };
      const removed = (removedEvent: any) => {
        if (removedEvent.element === event.element) {
          launch.assign = false;
        }
      };
      event.eventBus.on('commandStack.changed', changed);
      event.eventBus.on('shape.removed', removed);
      launch.stopWatching = () => {
        event.eventBus.off('commandStack.changed', changed);
        event.eventBus.off('shape.removed', removed);
      };
      launches.current.set(requestId, launch);
    },
    [messagesHref, sourceLocation],
  );

  useEffect(() => {
    const activeLaunches = launches.current;
    const onReturn = () => {
      if (document.visibilityState === 'visible') {
        void refresh();
      }
    };
    const onSaved = async (notification: MessageEvent) => {
      const data = notification.data;
      if (
        notification.origin !== window.location.origin ||
        data?.type !== MESSAGE_MODEL_SAVED ||
        typeof data.requestId !== 'string' ||
        typeof data.messageId !== 'string' ||
        typeof data.location !== 'string'
      ) {
        return;
      }
      const launch = launches.current.get(data.requestId);
      if (!launch || notification.source !== launch.popup) {
        return;
      }
      const catalog = await refresh();
      if (
        !catalog ||
        launches.current.get(data.requestId) !== launch ||
        !launch.assign ||
        messageRef(launch.event.element) !== launch.originalMessage
      ) {
        return;
      }
      // Never assign an out-of-scope definition or a shadowed ancestor's definition.
      const candidates = catalog.filter(
        (message) => message.identifier === data.messageId,
      );
      const nearest = findNearestAncestorLocation(
        sourceLocation,
        candidates.map((message) => message.location),
      );
      const saved = candidates.find(
        (message) =>
          message.location === nearest && message.location === data.location,
      );
      if (!saved) {
        return;
      }
      launch.assign = false;
      launch.event.applyMessage(saved);
    };
    window.addEventListener('focus', onReturn);
    document.addEventListener('visibilitychange', onReturn);
    window.addEventListener('message', onSaved);
    return () => {
      generation.current += 1;
      eventBus.current = null;
      activeLaunches.forEach((launch) => launch.stopWatching());
      activeLaunches.clear();
      window.removeEventListener('focus', onReturn);
      document.removeEventListener('visibilitychange', onReturn);
      window.removeEventListener('message', onSaved);
    };
  }, [diagramKey, refresh, sourceLocation]);

  return { onMessagesRequested, onLaunchMessageEditor };
}
