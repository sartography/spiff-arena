import { useSearchParams } from 'react-router-dom';

import 'react-datepicker/dist/react-datepicker.css';

import 'react-bootstrap-typeahead/css/Typeahead.css';
import 'react-bootstrap-typeahead/css/Typeahead.bs5.css';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import ProcessInstanceListTable from '../components/ProcessInstanceListTable';
import { getProcessModelFullIdentifierFromSearchParams } from '../helpers';

export default function ProcessInstanceList() {
  const [searchParams] = useSearchParams();
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
    return <h1>Process Instances</h1>;
  };
  return (
    <>
      {processInstanceBreadcrumbElement()}
      {processInstanceTitleElement()}
      <ProcessInstanceListTable additionalParams="with_relation_to_me=true" />
    </>
  );
}
