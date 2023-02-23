import { useEffect, useState } from 'react';
import HttpService from '../services/HttpService';
import TaskListTable from './TaskListTable';

export default function TasksWaitingForMyGroups() {
  const [userGroups, setUserGroups] = useState<string[] | null>(null);

  useEffect(() => {
    HttpService.makeCallToBackend({
      path: `/user-groups/for-current-user`,
      successCallback: setUserGroups,
    });
  }, [setUserGroups]);

  const tableComponents = () => {
    if (!userGroups) {
      return null;
    }

    return userGroups.map((userGroup: string) => {
      return (
        <TaskListTable
          apiPath="/tasks/for-my-groups"
          additionalParams={`user_group_identifier=${userGroup}`}
          paginationQueryParamPrefix={`group-tasks-${userGroup}`}
          tableTitle={`Tasks waiting for group: ${userGroup}`}
          tableDescription={`This is a list of tasks for the ${userGroup} group. They can be completed by any member of the group.`}
          paginationClassName="with-large-bottom-margin"
          textToShowIfEmpty="This group has no task assignments at this time."
          autoReload
          showWaitingOn={false}
          canCompleteAllTasks
        />
      );
    });
  };

  if (userGroups) {
    return <>{tableComponents()}</>;
  }
  return null;
}
