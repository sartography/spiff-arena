import TasksTable from './TasksTable';

export default function TasksWaitingForMe() {
  return (
    <TasksTable
      apiPath="/tasks/for-me"
      paginationQueryParamPrefix="tasks_waiting_for_me"
      tableTitle="Tasks waiting for me"
      tableDescription="These processes are waiting on you to complete the next task. All are processes created by others that are now actionable by you."
      paginationClassName="with-large-bottom-margin"
      autoReload
      showWaitingOn={false}
    />
  );
}
