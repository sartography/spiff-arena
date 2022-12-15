import { useSearchParams } from 'react-router-dom';

import 'react-datepicker/dist/react-datepicker.css';

import 'react-bootstrap-typeahead/css/Typeahead.css';
import 'react-bootstrap-typeahead/css/Typeahead.bs5.css';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import ProcessInstanceListTable from '../components/ProcessInstanceListTable';
import {getProcessModelFullIdentifierFromSearchParams, modifyProcessIdentifierForPathParam} from '../helpers';

export default function ProcessInstanceList() {
  const [searchParams] = useSearchParams();
  const processInstanceBreadcrumbElement = () => {
    const processModelFullIdentifier =
      getProcessModelFullIdentifierFromSearchParams(searchParams);
    if (processModelFullIdentifier === null) {
      return null;
    }
    const modifiedProcessModelId = modifyProcessIdentifierForPathParam(
      processModelFullIdentifier
    );

    return (
      <ProcessBreadcrumb
        hotCrumbs={[
          ['Process Groups', '/admin'],
          [
            `Process Model: ${processModelFullIdentifier}`,
            `process-models/${modifiedProcessModelId}`,
          ],
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
      <ProcessInstanceListTable />
    </>
  );
}
