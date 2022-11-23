import ProcessInstanceListTable from '../components/ProcessInstanceListTable';

export default function CompletedInstances() {
  return (
    <>
      <h2>My completed instances</h2>
      <p className="data-table-description">
        This is a list of instances you started that are now complete.
      </p>
      <ProcessInstanceListTable
        filtersEnabled={false}
        paginationQueryParamPrefix="my_completed_instances"
        perPageOptions={[2, 5, 25]}
        reportIdentifier="system_report_instances_initiated_by_me"
        showReports={false}
        textToShowIfEmpty="No completed instances"
      />
      <h2 style={{ marginTop: '1em' }}>Tasks actions by me</h2>
      <p className="data-table-description" />
      <ProcessInstanceListTable
        filtersEnabled={false}
        paginationQueryParamPrefix="my_completed_tasks"
        perPageOptions={[2, 5, 25]}
        reportIdentifier="system_report_instances_with_tasks_completed_by_me"
        showReports={false}
        textToShowIfEmpty="No completed instances"
      />
      <h2 style={{ marginTop: '1em' }}>With Tasks Completed By My Group</h2>
      <p className="data-table-description" />
      <ProcessInstanceListTable
        filtersEnabled={false}
        paginationQueryParamPrefix="group_completed_tasks"
        perPageOptions={[2, 5, 25]}
        reportIdentifier="system_report_instances_with_tasks_completed_by_my_groups"
        showReports={false}
        textToShowIfEmpty="No completed instances"
      />
    </>
  );
}
