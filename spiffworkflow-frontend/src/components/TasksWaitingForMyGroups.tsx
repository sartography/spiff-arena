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
          tableTitle={`Tarefas aguardando pelo grupo: ${userGroup}`}
          tableDescription={`Esta é uma lista de tarefas para o grupo ${userGroup}. Elas podem ser concluídas por qualquer membro do grupo.`}
          paginationClassName="with-large-bottom-margin"
          textToShowIfEmpty="Este grupo não possui atribuições de tarefas neste momento."
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
