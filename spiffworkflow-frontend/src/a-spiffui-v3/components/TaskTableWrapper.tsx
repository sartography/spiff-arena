import React from 'react';
import TaskTable from './TaskTable';

const TaskTableWrapper = ({ tasks, handleRunTask, getWaitingForTableCellComponent }) => (
  tasks && (
    <TaskTable
      tasks={tasks}
      handleRunTask={handleRunTask}
      getWaitingForTableCellComponent={getWaitingForTableCellComponent}
    />
  )
);

export default TaskTableWrapper;
