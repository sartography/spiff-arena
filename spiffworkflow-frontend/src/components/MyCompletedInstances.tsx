import ProcessInstanceListTable from './ProcessInstanceListTable';

const paginationQueryParamPrefix = 'my_completed_instances';

export default function MyCompletedInstances() {
  return (
    <ProcessInstanceListTable
      filtersEnabled={false}
      paginationQueryParamPrefix={paginationQueryParamPrefix}
      perPageOptions={[2, 5, 25]}
      reportIdentifier="system_report_completed_instances_initiated_by_me"
      showReports={false}
    />
  );
}
