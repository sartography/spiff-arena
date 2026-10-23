import { describe, expect, it } from 'vitest';

import {
  findNearestAncestorLocation,
  trimLocationSlashes,
} from './MessageHelper';

describe('trimLocationSlashes', () => {
  it.each([
    ['', ''],
    ['////', ''],
    ['parent/child', 'parent/child'],
    ['///order//residential///', 'order//residential'],
    [`order${'/'.repeat(10000)}`, 'order'],
  ])('trims only surrounding slashes', (location, expected) => {
    expect(trimLocationSlashes(location)).toBe(expected);
  });
});

describe('findNearestAncestorLocation', () => {
  it('returns the nearest matching ancestor location', () => {
    const nearestLocation = findNearestAncestorLocation('order/residential', [
      'order',
      'order/request-for-information',
      'shared',
    ]);

    expect(nearestLocation).toBe('order');
  });

  it('returns the exact location when present', () => {
    const nearestLocation = findNearestAncestorLocation('order/residential', [
      'order/residential',
      'order',
    ]);

    expect(nearestLocation).toBe('order/residential');
  });

  it('ignores surrounding slashes and preserves the original candidate', () => {
    expect(
      findNearestAncestorLocation('///order/residential///', [
        '/order/',
        '/order/residential/',
        'orders',
      ]),
    ).toBe('/order/residential/');
  });

  it('returns null when no ancestor location exists', () => {
    const nearestLocation = findNearestAncestorLocation('order/residential', [
      'shared/order',
      'training',
    ]);

    expect(nearestLocation).toBeNull();
  });
});
