// @ts-ignore
import { Breadcrumb, BreadcrumbItem } from '@carbon/react';
import { HotCrumbItem } from '../interfaces';

type OwnProps = {
  processModelId?: string;
  processGroupId?: string;
  linkProcessModel?: boolean;
  hotCrumbs?: HotCrumbItem[];
};

export default function ProcessBreadcrumb({
  processModelId,
  processGroupId,
  hotCrumbs,
  linkProcessModel = false,
}: OwnProps) {
  let processGroupBreadcrumb = null;
  let processModelBreadcrumb = null;
  if (hotCrumbs) {
    const lastItem = hotCrumbs.pop();
    if (lastItem === undefined) {
      return null;
    }
    const lastCrumb = (
      <BreadcrumbItem isCurrentPage>{lastItem[0]}</BreadcrumbItem>
    );
    const leadingCrumbLinks = hotCrumbs.map((crumb: any) => {
      const valueLabel = crumb[0];
      const url = crumb[1];
      return (
        <BreadcrumbItem key={valueLabel} href={url}>
          {valueLabel}
        </BreadcrumbItem>
      );
    });
    return (
      <Breadcrumb noTrailingSlash>
        {leadingCrumbLinks}
        {lastCrumb}
      </Breadcrumb>
    );
  }
  if (processModelId) {
    if (linkProcessModel) {
      processModelBreadcrumb = (
        <BreadcrumbItem
          href={`/admin/process-models/${processGroupId}/${processModelId}`}
        >
          {`Process Model: ${processModelId}`}
        </BreadcrumbItem>
      );
    } else {
      processModelBreadcrumb = (
        <BreadcrumbItem isCurrentPage>
          {`Process Model: ${processModelId}`}
        </BreadcrumbItem>
      );
    }
    processGroupBreadcrumb = (
      <BreadcrumbItem
        data-qa="process-group-breadcrumb-link"
        href={`/admin/process-groups/${processGroupId}`}
      >
        {`Process Group: ${processGroupId}`}
      </BreadcrumbItem>
    );
  } else if (processGroupId) {
    processGroupBreadcrumb = (
      <BreadcrumbItem isCurrentPage>
        {`Process Group: ${processGroupId}`}
      </BreadcrumbItem>
    );
  }

  return (
    <Breadcrumb noTrailingSlash>
      <BreadcrumbItem href="/admin">Process Groups</BreadcrumbItem>
      {processGroupBreadcrumb}
      {processModelBreadcrumb}
    </Breadcrumb>
  );
}
