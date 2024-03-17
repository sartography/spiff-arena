/**
 * There can be a lot of redundant requests for permissions (probably deps/contexts firing etc.)
 * This service provides a cache to check for already-processed perms.
 */
import { PermissionCheckResponseBody, PermissionsToCheck } from '../interfaces';

/** Map makes sense: no prototype to hack, high perf, easily wiped. */
const permissionsCache = new Map<string, any>();

const updatePermissionsCache = (
  permissionsResponse: PermissionCheckResponseBody
) => {
  if (Object.entries(permissionsResponse.results).length > 0) {
    Object.entries(permissionsResponse.results).forEach(
      ([path, permissions]) => {
        permissionsCache.set(path, permissions as Record<string, boolean>);
      }
    );
  }
};

/**
 * Look for the permissions in the cache. If satisfied, we don't need to make a backend call.
 * Then, create a response object and return it so we can complete any callbacks.
 */
const findPermissionsInCache = (
  permissionsToCheck: PermissionsToCheck
): PermissionCheckResponseBody | null => {
  const results: Record<string, Record<string, boolean>> = {};
  if (permissionsToCheck) {
    Object.entries(permissionsToCheck).forEach(([path]) => {
      const cachedPermissions = permissionsCache.get(path);
      if (cachedPermissions) {
        results[path] = cachedPermissions;
      }
    });
  }

  /**
   * Results must have content, and must be the same number of permissions as we're checking
   * TODO: This implementation can lead to redundant permissions requests if
   * the same individual permission is requested by different permission sets
   * (any perm in a set not found will trigger a backend call for the whole set).
   * This is erring on the side of caution for now, but a more robust individual
   * checker might be useful.
   */
  return Object.keys(results).length > 0 &&
    Object.keys(results).length === Object.keys(permissionsToCheck).length
    ? { results }
    : null;
};

// Don't allow retrieval or manipulation of the cache directly
const inspectPermissionsCache = () => {
  return new Map(permissionsCache);
};

const clearPermissionsCache = () => {
  permissionsCache.clear();
};

export {
  updatePermissionsCache,
  findPermissionsInCache,
  clearPermissionsCache,
  inspectPermissionsCache,
};
