import {
  updatePermissionsCache,
  inspectPermissionsCache,
  clearPermissionsCache,
} from './PermissionCacheService';

describe('updatePermissionsCache', () => {
  it('should update the permission cache with the provided permissions', () => {
    const permissionsToCheck = {
      '/path1': ['read', 'write'],
      '/path2': ['read'],
    };

    updatePermissionsCache(permissionsToCheck);
    expect(inspectPermissionsCache().get('/path1')).toEqual(['read', 'write']);
    expect(inspectPermissionsCache().get('/path2')).toEqual(['read']);
  });

  it('should update the permissions cache with the provided permissions', () => {
    const permissionsToCheck = {
      '/path1': ['read', 'write'],
      '/path2': ['read'],
    };

    updatePermissionsCache(permissionsToCheck);
    expect(inspectPermissionsCache().get('/path1')).toEqual(['read', 'write']);
    expect(inspectPermissionsCache().get('/path2')).toEqual(['read']);
  });

  it('should do nothing if permissionsToCheck is empty', () => {
    const permissionsToCheck = {};
    updatePermissionsCache(permissionsToCheck);
    expect(inspectPermissionsCache().size).toEqual(0);
  });

  it('should clear the permissions cache when told to', () => {
    const permissionsToCheck = {
      '/path1': ['read', 'write'],
      '/path2': ['read'],
    };

    updatePermissionsCache(permissionsToCheck);
    expect(inspectPermissionsCache().size).toEqual(2);
    clearPermissionsCache();
    expect(inspectPermissionsCache().size).toEqual(0);
  });
});
