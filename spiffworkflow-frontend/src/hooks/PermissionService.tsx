// We may need to update usage of Ability when we update.
// They say they are going to rename PureAbility to Ability and remove the old class.
import { AbilityBuilder, Ability } from '@casl/ability';
import { useContext, useEffect, useState } from 'react';
import { AbilityContext } from '../contexts/Can';
import { PermissionCheckResponseBody, PermissionsToCheck } from '../interfaces';
import HttpService from '../services/HttpService';

export const usePermissionFetcher = (
  permissionsToCheck: PermissionsToCheck
) => {
  const ability = useContext(AbilityContext);
  const [permissionsLoaded, setPermissionsLoaded] = useState<boolean>(false);

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
      setPermissionsLoaded(true);
    };

    HttpService.makeCallToBackend({
      path: `/permissions-check`,
      httpMethod: 'POST',
      successCallback: processPermissionResult,
      postBody: { requests_to_check: permissionsToCheck },
    });
  });

  return { ability, permissionsLoaded };
};
