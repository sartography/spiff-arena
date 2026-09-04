import { describe, expect, it } from 'vitest';
import { getRouterBasename, stripBasePath, withBasePath } from './basePath';

describe('frontend base path', () => {
  it('preserves root-path behavior by default', () => {
    expect(getRouterBasename('/')).toBeUndefined();
    expect(withBasePath('/login', '/')).toEqual('/login');
    expect(stripBasePath('/login', '/')).toEqual('/login');
  });

  it('uses the workflow base for full-page navigation', () => {
    expect(getRouterBasename('/workflow/')).toEqual('/workflow');
    expect(withBasePath('/login', '/workflow/')).toEqual('/workflow/login');
    expect(withBasePath('/workflow/login', '/workflow/')).toEqual(
      '/workflow/login',
    );
    expect(stripBasePath('/workflow/login', '/workflow/')).toEqual('/login');
  });

  it('leaves absolute urls untouched', () => {
    expect(withBasePath('https://example.com/foo', '/workflow/')).toEqual(
      'https://example.com/foo',
    );
    expect(withBasePath('mailto:hello@example.com', '/workflow/')).toEqual(
      'mailto:hello@example.com',
    );
  });
});
