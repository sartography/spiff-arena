// @ts-ignore
import { Breadcrumb, BreadcrumbItem } from '@carbon/react';
import { useEffect, useState } from 'react';
import { modifyProcessIdentifierForPathParam } from '../helpers';
import {
  HotCrumbItem,
  ProcessGroup,
  ProcessGroupLite,
  ProcessModel,
} from '../interfaces';
import HttpService from '../services/HttpService';

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
              entityToExplode as string
            )}`,
            successCallback: setProcessEntity,
          });
        } else if (entityType === 'process-group-id') {
          HttpService.makeCallToBackend({
            path: `/process-groups/${modifyProcessIdentifierForPathParam(
              entityToExplode as string
            )}`,
            successCallback: setProcessEntity,
          });
        } else {
          setProcessEntity(entityToExplode as any);
        }
      }
    };
    if (hotCrumbs) {
      hotCrumbs.forEach(explodeCrumbItemObject);
    }
  }, [setProcessEntity, hotCrumbs]);

  // eslint-disable-next-line sonarjs/cognitive-complexity
  const hotCrumbElement = () => {
    if (hotCrumbs) {
      const leadingCrumbLinks = hotCrumbs.map((crumb: any) => {
        if (
          'entityToExplode' in crumb &&
          processEntity &&
          processEntity.parent_groups
        ) {
          const breadcrumbs = processEntity.parent_groups.map(
            (parentGroup: ProcessGroupLite) => {
              const fullUrl = `/admin/process-groups/${modifyProcessIdentifierForPathParam(
                parentGroup.id
              )}`;
              return (
                <BreadcrumbItem key={parentGroup.id} href={fullUrl}>
                  {parentGroup.display_name}
                </BreadcrumbItem>
              );
            }
          );

          if (crumb.linkLastItem) {
            let apiBase = '/admin/process-groups';
            let dataQaTag = '';
            if (crumb.entityType.startsWith('process-model')) {
              apiBase = '/admin/process-models';
              dataQaTag = 'process-model-breadcrumb-link';
            }
            const fullUrl = `${apiBase}/${modifyProcessIdentifierForPathParam(
              processEntity.id
            )}`;
            breadcrumbs.push(
              <BreadcrumbItem
                key={processEntity.id}
                href={fullUrl}
                data-qa={dataQaTag}
              >
                {processEntity.display_name}
              </BreadcrumbItem>
            );
          } else {
            breadcrumbs.push(
              <BreadcrumbItem key={processEntity.id} isCurrentPage>
                {processEntity.display_name}
              </BreadcrumbItem>
            );
          }
          return breadcrumbs;
        }
        const valueLabel = crumb[0];
        const url = crumb[1];
        if (!url && valueLabel) {
          return (
            <BreadcrumbItem isCurrentPage key={valueLabel}>
              {valueLabel}
            </BreadcrumbItem>
          );
        }
        if (url && valueLabel) {
          return (
            <BreadcrumbItem key={valueLabel} href={url}>
              {valueLabel}
            </BreadcrumbItem>
          );
        }
        return null;
      });
      return <Breadcrumb noTrailingSlash>{leadingCrumbLinks}</Breadcrumb>;
    }
    return null;
  };

  return <Breadcrumb noTrailingSlash>{hotCrumbElement()}</Breadcrumb>;
}
