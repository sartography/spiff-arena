import TaskListTable from './TaskListTable';

const paginationQueryParamPrefix = 'tasks_for_my_open_processes';

export default function MyOpenProcesses() {
  return (
    <TaskListTable
      apiPath="/tasks/for-my-open-processes"
      paginationQueryParamPrefix={paginationQueryParamPrefix}
      tableTitle="Tarefas para minhas instâncias abertas"
      tableDescription="Essas tarefas são para processos que você iniciou e que não foram concluídos. Você pode não ter nenhuma ação a ser tomada no momento. Veja abaixo as tarefas que estão aguardando sua ação"
      paginationClassName="with-large-bottom-margin"
      textToShowIfEmpty="Não há tarefas para os processos que você iniciou neste momento."
      autoReload
      showStartedBy={false}
    />
  );
}
