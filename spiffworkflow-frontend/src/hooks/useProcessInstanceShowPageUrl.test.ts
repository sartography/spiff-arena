import { renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import useProcessInstanceShowPageUrl from './useProcessInstanceShowPageUrl';

const can = vi.fn();
const permissionFetcherMock = vi.fn();

vi.mock('react-router-dom', () => {
  return {
    useParams: () => ({ process_model_id: 'g:m', process_instance_id: '7' }),
  };
});

vi.mock('./PermissionService', () => {
  return {
    usePermissionFetcher: (permissionRequestData: Record<string, string[]>) => {
      permissionFetcherMock(permissionRequestData);
      return { ability: { can }, permissionsLoaded: true };
    },
  };
});

describe('useProcessInstanceShowPageUrl', () => {
  beforeEach(() => {
    can.mockReset();
    permissionFetcherMock.mockReset();
  });

  it('returns the for-me page url when the user can read its api path', () => {
    can.mockReturnValue(true);
    const { result } = renderHook(() =>
      useProcessInstanceShowPageUrl('for-me'),
    );
    expect(permissionFetcherMock).toHaveBeenCalledWith({
      '/v1.0/process-instances/for-me/g:m/7': ['GET'],
    });
    expect(result.current.processInstanceShowPageUrl).toBe(
      '/process-instances/for-me/g:m/7',
    );
  });

  it('returns null when the user may not view the page', () => {
    can.mockReturnValue(false);
    const { result } = renderHook(() => useProcessInstanceShowPageUrl('all'));
    expect(can).toHaveBeenCalledWith('GET', '/v1.0/process-instances/g:m/7');
    expect(result.current.processInstanceShowPageUrl).toBeNull();
  });
});
