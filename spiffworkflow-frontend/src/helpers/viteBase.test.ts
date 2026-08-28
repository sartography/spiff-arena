import { describe, expect, it } from 'vitest';
import { resolveBasePath } from '../../vite.config';

describe('Vite base path', () => {
  it('defaults to the site root', () => {
    expect(resolveBasePath({})).toEqual('/');
  });

  it('normalizes the configured workflow path', () => {
    expect(
      resolveBasePath({
        SPIFFWORKFLOW_FRONTEND_BUILD_TIME_BASE_PATH: 'workflow',
      }),
    ).toEqual('/workflow/');
  });
});
