import ProcessInstanceListTable from '../components/ProcessInstanceListTable';

export default function CompletedInstances() {
  return (
    <>
      <h1>Initiated By Me</h1>
      <ProcessInstanceListTable
        filtersEnabled={false}
        paginationQueryParamPrefix="my_completed_instances"
        perPageOptions={[2, 5, 25]}
        reportIdentifier="system_report_instances_initiated_by_me"
        showReports={false}
        textToShowIfEmpty={<p>No completed instances</p>}
      />
      <h1 style={{ marginTop: '1em' }}>With Tasks Completed By Me</h1>
      <ProcessInstanceListTable
        filtersEnabled={false}
        paginationQueryParamPrefix="my_completed_tasks"
        perPageOptions={[2, 5, 25]}
        reportIdentifier="system_report_instances_with_tasks_completed_by_me"
        showReports={false}
        textToShowIfEmpty={<p>No completed instances</p>}
      />
      <h1 style={{ marginTop: '1em' }}>With Tasks Completed By My Group</h1>
      <ProcessInstanceListTable
        filtersEnabled={false}
        paginationQueryParamPrefix="group_completed_tasks"
        perPageOptions={[2, 5, 25]}
        reportIdentifier="system_report_instances_with_tasks_completed_by_my_groups"
        showReports={false}
        textToShowIfEmpty={<p>No completed instances</p>}
      />
    </>
  );
}
