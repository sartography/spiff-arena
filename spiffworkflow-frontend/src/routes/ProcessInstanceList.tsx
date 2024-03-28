import { useSearchParams } from 'react-router-dom';

import 'react-datepicker/dist/react-datepicker.css';

import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import ProcessInstanceListTableWithFilters from '../components/ProcessInstanceListTableWithFilters';
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
    let headerText = 'My Process Instances';
    if (variant === 'all') {
      headerText = 'All Process Instances';
    }
    return { text: headerText };
  };

  return (
    <>
      <ProcessInstanceListTabs variant={variant} />
      <br />
      {processInstanceBreadcrumbElement()}
      <ProcessInstanceListTableWithFilters
        variant={variant}
        showActionsColumn
        header={processInstanceTitleElement()}
      />
    </>
  );
}
