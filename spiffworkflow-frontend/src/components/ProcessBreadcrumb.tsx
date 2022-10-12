import { Link } from 'react-router-dom';
import Breadcrumb from 'react-bootstrap/Breadcrumb';
import { BreadcrumbItem } from '../interfaces';

type OwnProps = {
  processModelId?: string;
  processGroupId?: string;
  linkProcessModel?: boolean;
  hotCrumbs?: BreadcrumbItem[];
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
    const lastCrumb = <Breadcrumb.Item active>{lastItem[0]}</Breadcrumb.Item>;
    const leadingCrumbLinks = hotCrumbs.map((crumb) => {
      const valueLabel = crumb[0];
      const url = crumb[1];
      return (
        <Breadcrumb.Item key={valueLabel} linkAs={Link} linkProps={{ to: url }}>
          {valueLabel}
        </Breadcrumb.Item>
      );
    });
    return (
      <Breadcrumb>
        {leadingCrumbLinks}
        {lastCrumb}
      </Breadcrumb>
    );
  }
  if (processModelId) {
    if (linkProcessModel) {
      processModelBreadcrumb = (
        <Breadcrumb.Item
          linkAs={Link}
          linkProps={{
            to: `/admin/process-models/${processGroupId}/${processModelId}`,
          }}
        >
          Process Model: {processModelId}
        </Breadcrumb.Item>
      );
    } else {
      processModelBreadcrumb = (
        <Breadcrumb.Item active>
          Process Model: {processModelId}
        </Breadcrumb.Item>
      );
    }
    processGroupBreadcrumb = (
      <Breadcrumb.Item
        linkAs={Link}
        data-qa="process-group-breadcrumb-link"
        linkProps={{ to: `/admin/process-groups/${processGroupId}` }}
      >
        Process Group: {processGroupId}
      </Breadcrumb.Item>
    );
  } else if (processGroupId) {
    processGroupBreadcrumb = (
      <Breadcrumb.Item active>Process Group: {processGroupId}</Breadcrumb.Item>
    );
  }

  return (
    <Breadcrumb>
      <Breadcrumb.Item linkAs={Link} linkProps={{ to: '/admin' }}>
        Process Groups
      </Breadcrumb.Item>
      {processGroupBreadcrumb}
      {processModelBreadcrumb}
    </Breadcrumb>
  );
}
