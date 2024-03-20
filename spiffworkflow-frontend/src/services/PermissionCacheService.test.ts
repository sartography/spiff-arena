import {
  updatePermissionsCache,
  inspectPermissionsCache,
  clearPermissionsCache,
} from './PermissionCacheService';

describe('updatePermissionsCache', () => {
  it('should update the permission cache with the provided permissions', () => {
    const permissionsResponse = {
      results: {
        '/path1': { GET: true },
        '/path2': { POST: true },
      },
    };
    updatePermissionsCache(permissionsResponse);
    // Note the cache stores the perms in an array
    expect(inspectPermissionsCache().get('/path1')).toEqual([{ GET: true }]);
    expect(inspectPermissionsCache().get('/path2')).toEqual([{ POST: true }]);
  });
  it('should update the permissions cache with the new permissions', () => {
    // Add more permissions to a given path
    const permissionsResponse = {
      results: {
        '/path1': { POST: true },
        '/path2': { GET: true },
      },
    };
    updatePermissionsCache(permissionsResponse);
    // Each path should now have the new permissions added to the existing ones
    expect(inspectPermissionsCache().get('/path1')).toEqual([
      { GET: true },
      { POST: true },
    ]);
    expect(inspectPermissionsCache().get('/path2')).toEqual([
      { POST: true },
      { GET: true },
    ]);
  });
  it('cache should be unchanged if results are empty', () => {
    const permissionsResponse = { results: {} };
    updatePermissionsCache(permissionsResponse);
    expect(inspectPermissionsCache().get('/path1')).toEqual([
      { GET: true },
      { POST: true },
    ]);
    expect(inspectPermissionsCache().get('/path2')).toEqual([
      { POST: true },
      { GET: true },
    ]);
    expect(inspectPermissionsCache().size).toEqual(2);
  });
  it('should clear the permissions cache when told to', () => {
    clearPermissionsCache();
    expect(inspectPermissionsCache().size).toEqual(0);
  });
});
