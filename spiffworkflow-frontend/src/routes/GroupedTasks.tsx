import TasksForMyOpenProcesses from '../components/TasksForMyOpenProcesses';
import TasksWaitingForMe from '../components/TasksWaitingForMe';
import TasksWaitingForMyGroups from '../components/TasksWaitingForMyGroups';

export default function GroupedTasks() {
  return (
    <>
      <TasksForMyOpenProcesses />
      <br />
      <TasksWaitingForMe />
      <br />
      <TasksWaitingForMyGroups />
    </>
  );
}
