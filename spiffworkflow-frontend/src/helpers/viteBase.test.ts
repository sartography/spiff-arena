import { describe, it, expect } from 'vitest';
import { resolveBasePath } from '../../vite.config';

describe('vite resolveBasePath', () => {
  it('defaults to /', () => {
    expect(resolveBasePath({})).toEqual('/');
    expect(
      resolveBasePath({
        SPIFFWORKFLOW_FRONTEND_BUILD_TIME_BASE_PATH: undefined,
      }),
    ).toEqual('/');
  });

  it('accepts SPIFFWORKFLOW_FRONTEND_BUILD_TIME_BASE_PATH', () => {
    expect(
      resolveBasePath({
        SPIFFWORKFLOW_FRONTEND_BUILD_TIME_BASE_PATH: '/workflow/',
      }),
    ).toEqual('/workflow/');
    expect(
      resolveBasePath({
        SPIFFWORKFLOW_FRONTEND_BUILD_TIME_BASE_PATH: '/workflow',
      }),
    ).toEqual('/workflow/');
    expect(
      resolveBasePath({
        SPIFFWORKFLOW_FRONTEND_BUILD_TIME_BASE_PATH: 'workflow',
      }),
    ).toEqual('/workflow/');
  });

  it('normalizes missing leading slash and ensures trailing slash', () => {
    expect(
      resolveBasePath({
        SPIFFWORKFLOW_FRONTEND_BUILD_TIME_BASE_PATH: 'a/b',
      }),
    ).toEqual('/a/b/');
  });

  it('uses / for empty or whitespace value', () => {
    expect(
      resolveBasePath({
        SPIFFWORKFLOW_FRONTEND_BUILD_TIME_BASE_PATH: '',
      }),
    ).toEqual('/');
    expect(
      resolveBasePath({
        SPIFFWORKFLOW_FRONTEND_BUILD_TIME_BASE_PATH: '   ',
      }),
    ).toEqual('/');
  });
});
