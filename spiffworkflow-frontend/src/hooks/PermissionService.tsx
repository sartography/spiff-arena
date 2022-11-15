import { AbilityBuilder, Ability } from '@casl/ability';
import { useContext, useEffect } from 'react';
import { AbilityContext } from '../contexts/Can';
import { PermissionCheckResponseBody, PermissionsToCheck } from '../interfaces';
import HttpService from '../services/HttpService';

export const usePermissionFetcher = (
  permissionsToCheck: PermissionsToCheck
) => {
  const ability = useContext(AbilityContext);

  useEffect(() => {
    const processPermissionResult = (result: PermissionCheckResponseBody) => {
      const { can, cannot, rules } = new AbilityBuilder(Ability);
      for (const [url, permissionVerbResults] of Object.entries(
        result.results
      )) {
        for (const [permissionVerb, hasPermission] of Object.entries(
          permissionVerbResults
        )) {
          if (hasPermission) {
            can(permissionVerb, url);
          } else {
            cannot(permissionVerb, url);
          }
        }
      }
      ability.update(rules);
    };
    HttpService.makeCallToBackend({
      path: `/permissions-check`,
      httpMethod: 'POST',
      successCallback: processPermissionResult,
      postBody: { requests_to_check: permissionsToCheck },
      // failureCallback: setErrorMessage,
    });
  });

  return { ability };
};
