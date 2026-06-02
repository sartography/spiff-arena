import { describe, expect, it } from 'vitest';

import { findNearestAncestorLocation } from './MessageHelper';

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

  it('returns null when no ancestor location exists', () => {
    const nearestLocation = findNearestAncestorLocation('order/residential', [
      'shared/order',
      'training',
    ]);

    expect(nearestLocation).toBeNull();
  });
});
