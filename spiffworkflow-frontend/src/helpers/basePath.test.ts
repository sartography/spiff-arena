/* eslint-disable sonarjs/no-duplicate-string */
import { describe, it, expect } from 'vitest';
import {
  normalizeBase,
  getBaseUrl,
  getRouterBasename,
  withBasePath,
  stripBasePath,
} from './basePath';

describe('normalizeBase', () => {
  it('defaults to /', () => {
    expect(normalizeBase(undefined)).toEqual('/');
    expect(normalizeBase('')).toEqual('/');
    expect(normalizeBase('   ')).toEqual('/');
  });

  it('ensures leading and trailing slash', () => {
    expect(normalizeBase('/')).toEqual('/');
    expect(normalizeBase('workflow')).toEqual('/workflow/');
    expect(normalizeBase('/workflow')).toEqual('/workflow/');
    expect(normalizeBase('/workflow/')).toEqual('/workflow/');
    expect(normalizeBase('workflow/')).toEqual('/workflow/');
  });

  it('trims whitespace', () => {
    expect(normalizeBase('  /workflow/  ')).toEqual('/workflow/');
  });
});

describe('getBaseUrl', () => {
  it('defaults to / when no base is configured', () => {
    expect(getBaseUrl(undefined)).toEqual('/');
    expect(getBaseUrl('/')).toEqual('/');
  });

  it('normalizes workflow base', () => {
    expect(getBaseUrl('/workflow/')).toEqual('/workflow/');
    expect(getBaseUrl('/workflow')).toEqual('/workflow/');
    expect(getBaseUrl('workflow')).toEqual('/workflow/');
  });
});

describe('getRouterBasename', () => {
  it('returns undefined for root', () => {
    expect(getRouterBasename('/')).toEqual(undefined);
    expect(getRouterBasename(undefined)).toEqual(undefined);
  });

  it('returns /workflow for workflow base', () => {
    expect(getRouterBasename('/workflow/')).toEqual('/workflow');
    expect(getRouterBasename('/workflow')).toEqual('/workflow');
    expect(getRouterBasename('workflow')).toEqual('/workflow');
  });

  it('handles multi-segment base', () => {
    expect(getRouterBasename('/a/b/')).toEqual('/a/b');
  });
});

describe('withBasePath', () => {
  it('returns path unchanged for root', () => {
    expect(withBasePath('/login', '/')).toEqual('/login');
    expect(withBasePath('/public/sign-out', '/')).toEqual('/public/sign-out');
  });

  it('prefixes path with workflow base', () => {
    expect(withBasePath('/login', '/workflow/')).toEqual('/workflow/login');
    expect(withBasePath('/public/sign-out', '/workflow/')).toEqual(
      '/workflow/public/sign-out',
    );
    expect(withBasePath('login', '/workflow/')).toEqual('/workflow/login');
  });

  it('does not double-prefix when path already has base', () => {
    expect(withBasePath('/workflow/login', '/workflow/')).toEqual(
      '/workflow/login',
    );
  });
});

describe('stripBasePath', () => {
  it('returns pathname unchanged for root', () => {
    expect(stripBasePath('/login', '/')).toEqual('/login');
    expect(stripBasePath('/workflow/login', '/')).toEqual('/workflow/login');
  });

  it('strips workflow base', () => {
    expect(stripBasePath('/workflow/login', '/workflow/')).toEqual('/login');
    expect(stripBasePath('/workflow', '/workflow/')).toEqual('/');
    expect(stripBasePath('/workflow/', '/workflow/')).toEqual('/');
    expect(stripBasePath('/', '/workflow/')).toEqual('/');
  });

  it('does not strip unrelated paths', () => {
    expect(stripBasePath('/other/login', '/workflow/')).toEqual('/other/login');
  });
});

describe('same base drives both assets and router', () => {
  it('produces consistent base and basename for /workflow/', () => {
    const base = getBaseUrl('/workflow/');
    const basename = getRouterBasename('/workflow/');
    expect(base).toEqual('/workflow/');
    expect(basename).toEqual('/workflow');
    // Asset URLs would be `${base}assets/...`
    expect(`${base}assets/index.js`).toEqual('/workflow/assets/index.js');
    // Router path would be `${basename}/some/route`
    expect(`${basename}/tasks`).toEqual('/workflow/tasks');
  });

  it('produces consistent root for /', () => {
    const base = getBaseUrl('/');
    const basename = getRouterBasename('/');
    expect(base).toEqual('/');
    expect(basename).toEqual(undefined);
    expect(`${base}assets/index.js`).toEqual('/assets/index.js');
  });
});
