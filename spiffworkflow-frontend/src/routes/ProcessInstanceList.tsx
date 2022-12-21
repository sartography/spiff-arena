import { useNavigate, useSearchParams } from 'react-router-dom';

import 'react-datepicker/dist/react-datepicker.css';

import 'react-bootstrap-typeahead/css/Typeahead.css';
import 'react-bootstrap-typeahead/css/Typeahead.bs5.css';
// @ts-ignore
import { Tabs, TabList, Tab } from '@carbon/react';
import { Can } from '@casl/react';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import ProcessInstanceListTable from '../components/ProcessInstanceListTable';
import { getProcessModelFullIdentifierFromSearchParams } from '../helpers';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import { PermissionsToCheck } from '../interfaces';
import { usePermissionFetcher } from '../hooks/PermissionService';

type OwnProps = {
  variant: string;
};

export default function ProcessInstanceList({ variant }: OwnProps) {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const { targetUris } = useUriListForPermissions();
  const permissionRequestData: PermissionsToCheck = {
    [targetUris.processInstanceListPath]: ['GET'],
  };
  const { ability } = usePermissionFetcher(permissionRequestData);

  const processInstanceBreadcrumbElement = () => {
    const processModelFullIdentifier =
      getProcessModelFullIdentifierFromSearchParams(searchParams);
    if (processModelFullIdentifier === null) {
      return null;
    }

    return (
      <ProcessBreadcrumb
        hotCrumbs={[
          ['Process Groups', '/admin'],
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

  let selectedTabIndex = 0;
  if (variant === 'all') {
    selectedTabIndex = 1;
  }
  return (
    <>
      <Tabs selectedIndex={selectedTabIndex}>
        <TabList aria-label="List of tabs">
          <Tab
            title="Only show process instances for the current user."
            onClick={() => {
              navigate('/admin/process-instances/for-me');
            }}
          >
            For Me
          </Tab>
          <Can I="GET" a={targetUris.processInstanceListPath} ability={ability}>
            <Tab
              title="Show all process instances for all users."
              onClick={() => {
                navigate('/admin/process-instances/all');
              }}
            >
              All
            </Tab>
          </Can>
        </TabList>
      </Tabs>
      <br />
      {processInstanceBreadcrumbElement()}
      {processInstanceTitleElement()}
      <ProcessInstanceListTable variant={variant} />
    </>
  );
}
