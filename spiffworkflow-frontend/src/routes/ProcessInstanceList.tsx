import { useSearchParams } from 'react-router-dom';

import 'react-datepicker/dist/react-datepicker.css';

import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import ProcessInstanceListTable from '../components/ProcessInstanceListTable';
import {
  getProcessModelFullIdentifierFromSearchParams,
  setPageTitle,
} from '../helpers';
import ProcessInstanceListTabs from '../components/ProcessInstanceListTabs';

type OwnProps = {
  variant: string;
};

export default function ProcessInstanceList({ variant }: OwnProps) {
  const [searchParams] = useSearchParams();
  setPageTitle(['Process Instances']);

  const processInstanceBreadcrumbElement = () => {
    const processModelFullIdentifier =
      getProcessModelFullIdentifierFromSearchParams(searchParams);
    if (processModelFullIdentifier === null) {
      return null;
    }

    return (
      <ProcessBreadcrumb
        hotCrumbs={[
          ['Process Groups', '/process-groups'],
          {
            entityToExplode: processModelFullIdentifier,
            entityType: 'process-model-id',
            linkLastItem: true,
          },
          ['Process Instances'],
        ]}
      />
    );
  };

  const processInstanceTitleElement = () => {
    if (variant === 'all') {
      return <h1>All Process Instances</h1>;
    }
    return <h1>My Process Instances</h1>;
  };

  return (
    <>
      <ProcessInstanceListTabs variant={variant} />
      <br />
      {processInstanceBreadcrumbElement()}
      {processInstanceTitleElement()}
      <ProcessInstanceListTable variant={variant} showActionsColumn />
    </>
  );
}
