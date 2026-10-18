import { createElement, PropsWithChildren } from 'react';
import { act, renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import HttpService from '../services/HttpService';
import useProcessInstanceShowPageUrl, {
  processInstanceShowPagePath,
  useProcessInstancePageAccess,
} from './useProcessInstanceShowPageUrl';

vi.mock('react-router-dom', () => ({
  useParams: () => ({ process_model_id: 'g:m', process_instance_id: '7' }),
}));
vi.mock('../services/HttpService', () => ({
  default: { makeCallToBackend: vi.fn() },
}));

const requests = () => vi.mocked(HttpService.makeCallToBackend).mock.calls;
const respond = (index: number, results: Record<string, { GET: boolean }>) => {
  act(() => requests()[index][0].successCallback({ results }));
};
const wrapper = () => {
  const client = new QueryClient();
  return function QueryWrapper({ children }: PropsWithChildren) {
    return createElement(QueryClientProvider, { client }, children);
  };
};

beforeEach(() => vi.clearAllMocks());

describe('process instance page access', () => {
  it.each(['for-me', 'all'])('checks the %s page API path', async (variant) => {
    const url = processInstanceShowPagePath(variant, 'g/m', 7);
    const { result } = renderHook(
      () => useProcessInstanceShowPageUrl(variant),
      {
        wrapper: wrapper(),
      },
    );
    expect(result.current).toEqual({
      processInstanceShowPageUrl: null,
      permissionsLoaded: false,
    });
    expect(requests()[0][0].postBody).toEqual({
      requests_to_check: { [`/v1.0${url}`]: ['GET'] },
    });
    respond(0, { [`/v1.0${url}`]: { GET: true } });
    await waitFor(() =>
      expect(result.current.processInstanceShowPageUrl).toBe(url),
    );
    expect(result.current.permissionsLoaded).toBe(true);
  });

  it('does not link to a denied page', async () => {
    const { result } = renderHook(
      () => useProcessInstanceShowPageUrl('for-me'),
      {
        wrapper: wrapper(),
      },
    );
    respond(0, { '/v1.0/process-instances/for-me/g:m/7': { GET: false } });
    await waitFor(() => expect(result.current.permissionsLoaded).toBe(true));
    expect(result.current.processInstanceShowPageUrl).toBeNull();
  });

  it('batches and deduplicates exact paths, preserving per-instance denies', async () => {
    const allowed = '/process-instances/for-me/g:m/7';
    const denied = '/process-instances/for-me/g:m/8';
    const { result } = renderHook(
      () => useProcessInstancePageAccess([denied, allowed, allowed]),
      { wrapper: wrapper() },
    );
    expect(requests()).toHaveLength(1);
    expect(requests()[0][0].postBody).toEqual({
      requests_to_check: {
        [`/v1.0${allowed}`]: ['GET'],
        [`/v1.0${denied}`]: ['GET'],
      },
    });
    respond(0, {
      [`/v1.0${allowed}`]: { GET: true },
      [`/v1.0${denied}`]: { GET: false },
    });
    await waitFor(() => expect(result.current.canReadPage(allowed)).toBe(true));
    expect(result.current.canReadPage(denied)).toBe(false);
  });

  it('does not reuse stale results when the requested pages change', async () => {
    const { result, rerender } = renderHook(
      ({ urls }) => useProcessInstancePageAccess(urls),
      { initialProps: { urls: ['/old'] }, wrapper: wrapper() },
    );
    respond(0, { '/v1.0/old': { GET: true } });
    await waitFor(() => expect(result.current.canReadPage('/old')).toBe(true));
    rerender({ urls: ['/new'] });
    expect(result.current.permissionsLoaded).toBe(false);
    expect(result.current.canReadPage('/old')).toBe(false);
    respond(1, { '/v1.0/new': { GET: false } });
    await waitFor(() => expect(result.current.permissionsLoaded).toBe(true));
    expect(result.current.canReadPage('/new')).toBe(false);
  });

  it('ignores late results from a previous page', async () => {
    const { result, rerender } = renderHook(
      ({ urls }) => useProcessInstancePageAccess(urls),
      { initialProps: { urls: ['/old'] }, wrapper: wrapper() },
    );
    rerender({ urls: ['/new'] });
    respond(1, { '/v1.0/new': { GET: false } });
    await waitFor(() => expect(result.current.permissionsLoaded).toBe(true));
    respond(0, { '/v1.0/old': { GET: true } });
    expect(result.current.canReadPage('/old')).toBe(false);
    expect(result.current.canReadPage('/new')).toBe(false);
  });

  it('does not request permissions for an empty table', () => {
    const { result } = renderHook(() => useProcessInstancePageAccess([]), {
      wrapper: wrapper(),
    });
    expect(requests()).toHaveLength(0);
    expect(result.current.permissionsLoaded).toBe(true);
  });

  it.each(['failureCallback', 'onUnauthorized'] as const)(
    'fails closed without hanging on %s',
    async (callback) => {
      const { result } = renderHook(
        () => useProcessInstancePageAccess(['/page']),
        {
          wrapper: wrapper(),
        },
      );
      act(() =>
        requests()[0][0][callback]!(new Error('Permission check failed')),
      );
      await waitFor(() => expect(result.current.permissionsLoaded).toBe(true));
      expect(result.current.canReadPage('/page')).toBe(false);
    },
  );
});
