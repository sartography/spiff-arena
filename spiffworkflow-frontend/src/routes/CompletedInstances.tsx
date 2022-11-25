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
        textToShowIfEmpty="You have no completed instances at this time."
        paginationClassName="with-large-bottom-margin"
        autoReload
      />
      <h2>Tasks completed by me</h2>
      <p className="data-table-description">
        This is a list of instances where you have completed tasks.
      </p>
      <ProcessInstanceListTable
        filtersEnabled={false}
        paginationQueryParamPrefix="my_completed_tasks"
        perPageOptions={[2, 5, 25]}
        reportIdentifier="system_report_instances_with_tasks_completed_by_me"
        showReports={false}
        textToShowIfEmpty="You have no completed tasks at this time."
        paginationClassName="with-large-bottom-margin"
      />
      <h2>Tasks completed by my groups</h2>
      <p className="data-table-description">
        This is a list of instances with tasks that were completed by groups you
        belong to.
      </p>
      <ProcessInstanceListTable
        filtersEnabled={false}
        paginationQueryParamPrefix="group_completed_tasks"
        perPageOptions={[2, 5, 25]}
        reportIdentifier="system_report_instances_with_tasks_completed_by_my_groups"
        showReports={false}
        textToShowIfEmpty="Your group has no completed tasks at this time."
      />
    </>
  );
}
