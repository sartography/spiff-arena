import { useEffect, useState } from 'react';
import HttpService from '../services/HttpService';
import TasksTable from './TasksTable';

export default function TasksWaitingForMyGroups() {
  const [userGroups, setUserGroups] = useState<string[] | null>(null);

  useEffect(() => {
    HttpService.makeCallToBackend({
      path: `/tasks/user-groups`,
      successCallback: setUserGroups,
    });
  }, [setUserGroups]);
  const tableComponents = () => {
    if (!userGroups) {
      return null;
    }

    return userGroups.map((userGroup: string) => {
      return (
        <TasksTable
          apiPath="/tasks/for-my-groups"
          additionalParams={`group_identifier=${userGroup}`}
          paginationQueryParamPrefix={`group-tasks-${userGroup}`}
          tableTitle={`Tasks waiting for ${userGroup} group`}
          tableDescription={`This is a list of tasks for the ${userGroup} group and can be completed by any member of the group.`}
          paginationClassName="with-large-bottom-margin"
          autoReload
          showWaitingOn={false}
        />
      );
    });
  };

  if (userGroups) {
    return <>{tableComponents()}</>;
  }
  return null;
}
