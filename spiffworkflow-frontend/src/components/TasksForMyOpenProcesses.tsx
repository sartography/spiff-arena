import TaskListTable from './TaskListTable';

const paginationQueryParamPrefix = 'tasks_for_my_open_processes';

export default function MyOpenProcesses() {
  return (
    <TaskListTable
      apiPath="/tasks/for-my-open-processes"
      paginationQueryParamPrefix={paginationQueryParamPrefix}
      tableTitle="Tasks for my open instances"
      tableDescription="These tasks are for processes you started which are not complete. You may not have an action to take at this time. See below for tasks waiting on you."
      paginationClassName="with-large-bottom-margin"
      textToShowIfEmpty="There are no tasks for processes you started at this time."
      autoReload
      showStartedBy={false}
    />
  );
}
