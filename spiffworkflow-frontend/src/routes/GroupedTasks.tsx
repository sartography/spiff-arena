import MyTasksForProcessesStartedByOthers from '../components/MyTasksForProcessesStartedByOthers';
import TasksForMyOpenProcesses from '../components/TasksForMyOpenProcesses';

export default function GroupedTasks() {
  return (
    <>
      <TasksForMyOpenProcesses />
      <br />
      <MyTasksForProcessesStartedByOthers />
    </>
  );
}
