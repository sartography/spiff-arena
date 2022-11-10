// @ts-ignore
import { Breadcrumb, BreadcrumbItem } from '@carbon/react';
import { splitProcessModelId } from '../helpers';
import { HotCrumbItem } from '../interfaces';

type OwnProps = {
  processModelId?: string;
  processGroupId?: string;
  linkProcessModel?: boolean;
  hotCrumbs?: HotCrumbItem[];
};

const explodeCrumb = (crumb: HotCrumbItem) => {
  const url: string = crumb[1] || '';
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [endingUrlType, processModelId, link] = url.split(':');
  const processModelIdSegments = splitProcessModelId(processModelId);
  const paths: string[] = [];
  const lastPathItem = processModelIdSegments.pop();
  const breadcrumbItems = processModelIdSegments.map(
    (processModelIdSegment: string) => {
      paths.push(processModelIdSegment);
      const fullUrl = `/admin/process-groups/${paths.join(':')}`;
      return (
        <BreadcrumbItem key={processModelIdSegment} href={fullUrl}>
          {processModelIdSegment}
        </BreadcrumbItem>
      );
    }
  );
  if (link === 'link') {
    if (lastPathItem !== undefined) {
      paths.push(lastPathItem);
    }
    // process_models to process-models
    const lastUrl = `/admin/${endingUrlType
      .replace('_', '-')
      .replace(/s*$/, 's')}/${paths.join(':')}`;
    breadcrumbItems.push(
      <BreadcrumbItem key={lastPathItem} href={lastUrl}>
        {lastPathItem}
      </BreadcrumbItem>
    );
  } else {
    breadcrumbItems.push(
      <BreadcrumbItem isCurrentPage key={lastPathItem}>
        {lastPathItem}
      </BreadcrumbItem>
    );
  }
  return breadcrumbItems;
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
    const leadingCrumbLinks = hotCrumbs.map((crumb: any) => {
      const valueLabel = crumb[0];
      const url = crumb[1];
      if (!url) {
        return (
          <BreadcrumbItem isCurrentPage key={valueLabel}>
            {valueLabel}
          </BreadcrumbItem>
        );
      }
      if (url && url.match(/^process[_-](model|group)s?:/)) {
        return explodeCrumb(crumb);
      }
      return (
        <BreadcrumbItem key={valueLabel} href={url}>
          {valueLabel}
        </BreadcrumbItem>
      );
    });
    return <Breadcrumb noTrailingSlash>{leadingCrumbLinks}</Breadcrumb>;
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
