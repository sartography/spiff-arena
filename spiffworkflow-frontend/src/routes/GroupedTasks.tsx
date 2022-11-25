import TasksForMyOpenProcesses from '../components/TasksForMyOpenProcesses';
import TasksWaitingForMe from '../components/TasksWaitingForMe';
import TasksWaitingForMyGroups from '../components/TasksWaitingForMyGroups';

export default function GroupedTasks() {
  return (
    <>
      {/* be careful moving these around since the first two have with-large-bottom-margin in order to get some space between the three table sections */}
      <TasksForMyOpenProcesses />
      <TasksWaitingForMe />
      <TasksWaitingForMyGroups />
    </>
  );
}
