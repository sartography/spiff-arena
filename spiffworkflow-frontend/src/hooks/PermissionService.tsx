// We may need to update usage of Ability when we update.
// They say they are going to rename PureAbility to Ability and remove the old class.
import { AbilityBuilder, Ability } from '@casl/ability';
import { useContext, useEffect, useState } from 'react';
import { AbilityContext } from '../contexts/Can';
import { PermissionCheckResponseBody, PermissionsToCheck } from '../interfaces';
import HttpService from '../services/HttpService';

export const checkPermissions = (
  permissionsToCheck: PermissionsToCheck,
  successCallback: Function
) => {
  if (Object.keys(permissionsToCheck).length !== 0) {
    HttpService.makeCallToBackend({
      path: `/permissions-check`,
      httpMethod: 'POST',
      successCallback,
      postBody: { requests_to_check: permissionsToCheck },
    });
  }
};

export const usePermissionFetcher = (
  permissionsToCheck: PermissionsToCheck
) => {
  const ability = useContext(AbilityContext);
  const [permissionsLoaded, setPermissionsLoaded] = useState<boolean>(false);
  const [loadedPermissions, setLoadedPermissions] = useState<Array<any>>([]);

  useEffect(() => {
    const processPermissionResult = (result: PermissionCheckResponseBody) => {
      const oldRules = ability.rules;
      const { can, cannot, rules } = new AbilityBuilder(Ability);
      Object.keys(result.results).forEach((url: string) => {
        const permissionVerbResults = result.results[url];
        Object.keys(permissionVerbResults).forEach((permissionVerb: string) => {
          const hasPermission = permissionVerbResults[permissionVerb];
          if (hasPermission) {
            can(permissionVerb, url);
          } else {
            cannot(permissionVerb, url);
          }
        });
      });
      oldRules.forEach((oldRule: any) => {
        if (oldRule.inverted) {
          cannot(oldRule.action, oldRule.subject);
        } else {
          can(oldRule.action, oldRule.subject);
        }
      });
      ability.update(rules);
      setLoadedPermissions((prev) => [...prev, result]);
      setPermissionsLoaded(true);
    };

    /**
     * There can be a lot of requests for permissions (probably based on dependencies everywhere)
     * That can lead to piles of redundant permission checks (perf, network chatter, console clutter).
     * So, we need to check if we've already checked the permissions we're about to check.
     */

    // First, get the stored result with the same key length as the permission request
    // (We could probably do these individually, but hedging on more precision for time being).
    const permCount = loadedPermissions.filter((perm) => {
      if (
        Object.keys(perm.results).length ===
        Object.keys(permissionsToCheck).length
      ) {
        return perm.results;
      }

      return null;
    });

    // Now, check if the perms to check are the same as the perms that were checked
    let foundPerm = null;
    permCount.forEach((perm) => {
      let foundAll = true;
      Object.keys(permissionsToCheck).forEach((url) => {
        if (!perm.results[url]) {
          foundAll = false;
        }
      });

      if (foundAll) {
        foundPerm = perm;
      }
    });

    // If a permission object with the same number of keys, and the same keys, is not found,
    // then we need to check the permissions.
    if (!foundPerm) {
      checkPermissions(permissionsToCheck, processPermissionResult);
    }
  });

  return { ability, permissionsLoaded };
};
