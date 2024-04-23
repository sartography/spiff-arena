import TaskListTable from './TaskListTable';

export default function TasksWaitingForMe() {
  return (
    <TaskListTable
      apiPath="/tasks/for-me"
      paginationQueryParamPrefix="tasks_waiting_for_me"
      tableTitle="Tarefas aguardando por mim"
      tableDescription="Esses processos estão aguardando você para completar a próxima tarefa. Todos são processos criados por outros que agora podem ser realizados por você."
      paginationClassName="with-large-bottom-margin"
      textToShowIfEmpty="Não há tarefas aguardando por você."
      autoReload
      showWaitingOn={false}
      canCompleteAllTasks
    />
  );
}
