import { Typography } from '@mui/material';
import Breadcrumbs from '@mui/material/Breadcrumbs';

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { modifyProcessIdentifierForPathParam } from '../helpers';
import {
  HotCrumbItem,
  HotCrumbItemArray,
  HotCrumbItemObject,
  ProcessGroup,
  ProcessGroupLite,
  ProcessModel,
} from '../interfaces';
import HttpService from '../services/HttpService';

// it is recommend to use a state for hotCrumbs so ProcessBreadCrumb does not attmept
// to re-render. This is because javascript cannot tell if an array or object has changed
// but react states can. If we simply initialize a ProcessBreadCrumb when
// the component that uses it renders, we may get a request to process model show
// every time a state changes in the parent component (any state, not even a related state).
// For an example of usage see TaskShow.
type OwnProps = {
  hotCrumbs?: HotCrumbItem[];
};

export default function ProcessBreadcrumb({ hotCrumbs }: OwnProps) {
  const [processEntity, setProcessEntity] = useState<
    ProcessGroup | ProcessModel | null
  >(null);

  useEffect(() => {
    const explodeCrumbItemObject = (crumb: HotCrumbItem) => {
      if ('entityToExplode' in crumb) {
        const { entityToExplode, entityType } = crumb;
        if (entityType === 'process-model-id') {
          HttpService.makeCallToBackend({
            path: `/process-models/${modifyProcessIdentifierForPathParam(
              entityToExplode as string,
            )}`,
            successCallback: setProcessEntity,
            onUnauthorized: () => {},
            failureCallback: (error: any) =>
              console.error(
                `Failed to load process model for breadcrumb. Error was: ${error.message}`,
              ),
          });
        } else if (entityType === 'process-group-id') {
          HttpService.makeCallToBackend({
            path: `/process-groups/${modifyProcessIdentifierForPathParam(
              entityToExplode as string,
            )}`,
            successCallback: setProcessEntity,
            onUnauthorized: () => {},
            failureCallback: (error: any) =>
              console.error(
                `Failed to load process group for breadcrumb. Error was: ${error.message}`,
              ),
          });
        } else {
          setProcessEntity(entityToExplode as any);
        }
      }
    };
    if (hotCrumbs) {
      hotCrumbs.forEach(explodeCrumbItemObject);
    }
  }, [hotCrumbs]);

  const checkPermissions = (crumb: HotCrumbItemObject) => {
    if (!crumb.checkPermission) {
      return true;
    }
    return (
      processEntity &&
      'actions' in processEntity &&
      processEntity.actions &&
      'read' in processEntity.actions
    );
  };

  // eslint-disable-next-line sonarjs/cognitive-complexity
  const hotCrumbElement = () => {
    if (hotCrumbs) {
      const leadingCrumbLinks = hotCrumbs.map(
        (crumb: HotCrumbItemArray | HotCrumbItemObject) => {
          if (
            'entityToExplode' in crumb &&
            processEntity &&
            processEntity.parent_groups &&
            checkPermissions(crumb)
          ) {
            const breadcrumbs = processEntity.parent_groups.map(
              (parentGroup: ProcessGroupLite) => {
                const fullUrl = `/process-groups/${modifyProcessIdentifierForPathParam(
                  parentGroup.id,
                )}`;
                return (
                  <Link key={parentGroup.id} to={fullUrl}>
                    {parentGroup.display_name}
                  </Link>
                );
              },
            );

            if (crumb.linkLastItem) {
              let apiBase = '/process-groups';
              let dataQaTag = '';
              if (crumb.entityType.startsWith('process-model')) {
                apiBase = '/process-models';
                dataQaTag = 'process-model-breadcrumb-link';
              }
              const fullUrl = `${apiBase}/${modifyProcessIdentifierForPathParam(
                processEntity.id,
              )}`;
              breadcrumbs.push(
                <Link key={processEntity.id} to={fullUrl} data-qa={dataQaTag}>
                  {processEntity.display_name}
                </Link>,
              );
            } else {
              breadcrumbs.push(
                <Typography key={processEntity.id} color="text.primary">
                  {processEntity.display_name}
                </Typography>,
              );
            }
            return breadcrumbs;
          }
          if (Array.isArray(crumb)) {
            const valueLabel = crumb[0];
            const url = crumb[1];
            if (!url && valueLabel) {
              return (
                <Typography key={valueLabel} color="text.primary">
                  {valueLabel}
                </Typography>
              );
            }
            if (url && valueLabel) {
              return (
                <Link key={valueLabel} to={url}>
                  {valueLabel}
                </Link>
              );
            }
          }
          return null;
        },
      );
      return (
        <Breadcrumbs className="spiff-breadcrumb">
          {leadingCrumbLinks}
        </Breadcrumbs>
      );
    }
    return null;
  };

  return <>{hotCrumbElement()}</>;
}
