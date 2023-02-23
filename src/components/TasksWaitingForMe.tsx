import TaskListTable from './TaskListTable';

export default function TasksWaitingForMe() {
  return (
    <TaskListTable
      apiPath="/tasks/for-me"
      paginationQueryParamPrefix="tasks_waiting_for_me"
      tableTitle="Tasks waiting for me"
      tableDescription="These processes are waiting on you to complete the next task. All are processes created by others that are now actionable by you."
      paginationClassName="with-large-bottom-margin"
      textToShowIfEmpty="No tasks are waiting for you."
      autoReload
      showWaitingOn={false}
      canCompleteAllTasks
    />
  );
}
