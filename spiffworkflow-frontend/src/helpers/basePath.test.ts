import { describe, expect, it } from 'vitest';
import { getRouterBasename, stripBasePath, withBasePath } from './basePath';

describe('frontend base path', () => {
  const WORKFLOW_BASE = '/workflow/';

  it('preserves root-path behavior by default', () => {
    expect(getRouterBasename('/')).toBeUndefined();
    expect(withBasePath('/login', '/')).toEqual('/login');
    expect(stripBasePath('/login', '/')).toEqual('/login');
  });

  it('uses the workflow base for full-page navigation', () => {
    expect(getRouterBasename(WORKFLOW_BASE)).toEqual('/workflow');
    expect(withBasePath('/login', WORKFLOW_BASE)).toEqual('/workflow/login');
    expect(withBasePath('/workflow/login', WORKFLOW_BASE)).toEqual(
      '/workflow/login',
    );
    expect(stripBasePath('/workflow/login', WORKFLOW_BASE)).toEqual('/login');
  });

  it('leaves http(s) absolute urls untouched', () => {
    expect(withBasePath('https://example.com/foo', WORKFLOW_BASE)).toEqual(
      'https://example.com/foo',
    );
    expect(withBasePath('http://example.com/foo', WORKFLOW_BASE)).toEqual(
      'http://example.com/foo',
    );
  });

  it('neutralizes executable schemes by routing them same-origin', () => {
    expect(withBasePath('javascript:alert(1)', WORKFLOW_BASE)).toEqual(
      '/workflow/javascript:alert(1)',
    );
    expect(withBasePath('data:text/html,<h1>hi</h1>', WORKFLOW_BASE)).toEqual(
      '/workflow/data:text/html,<h1>hi</h1>',
    );
    expect(withBasePath('vbscript:msgbox(1)', WORKFLOW_BASE)).toEqual(
      '/workflow/vbscript:msgbox(1)',
    );
    expect(withBasePath('JAVASCRIPT:alert(1)', WORKFLOW_BASE)).toEqual(
      '/workflow/JAVASCRIPT:alert(1)',
    );
  });
});
