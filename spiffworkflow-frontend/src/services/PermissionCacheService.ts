/**
 * There can be a lot of redundant requests for permissions (probably deps/contexts firing etc.)
 * This service provides a cache to check for already-processed perms.
 */
import { PermissionsToCheck } from '../interfaces';

/** Map makes sense: no prototype to hack, high perf, easily wiped. */
const permissionCache = new Map<string, Array<string>>();

const updatePermissionsCache = (permissionsToCheck: PermissionsToCheck) => {
  Object.keys(permissionsToCheck).forEach((path: string) => {
    permissionCache.set(path, permissionsToCheck[path]);
  });
};

/**
 * TODO: This can lead to redundant permissions requests if the same individual permission
 * is requested by different permission sets (any perm in a set not found will
 * trigger a backend call for the whole set).
 * This is erring on the side of caution for now, but a more robust individual
 * checker might be useful.
 */
const findPermissionsInCache = (permissionsToCheck: PermissionsToCheck) => {
  let foundAllPerms = true;
  Object.keys(permissionsToCheck).forEach((path: string) => {
    if (!permissionCache.has(path)) {
      foundAllPerms = false;
    }
  });
  return foundAllPerms;
};

const clearPermissionsCache = () => {
  permissionCache.clear();
};

export {
  updatePermissionsCache,
  findPermissionsInCache,
  clearPermissionsCache,
};
