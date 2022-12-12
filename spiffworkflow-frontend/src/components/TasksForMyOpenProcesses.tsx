import TasksTable from './TasksTable';

const paginationQueryParamPrefix = 'tasks_for_my_open_processes';

export default function MyOpenProcesses() {
  return (
    <TasksTable
      apiPath="/tasks/for-my-open-processes"
      paginationQueryParamPrefix={paginationQueryParamPrefix}
      tableTitle="My open instances"
      tableDescription="These tasks are for processes you started which are not complete. You may not have an action to take at this time. See below for tasks waiting on you."
      paginationClassName="with-large-bottom-margin"
      autoReload
      showStartedBy={false}
    />
  );
}
