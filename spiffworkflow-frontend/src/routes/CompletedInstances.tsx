import { useEffect, useState } from 'react';
import ProcessInstanceListTable from '../components/ProcessInstanceListTable';
import HttpService from '../services/HttpService';

export default function CompletedInstances() {
  const [userGroups, setUserGroups] = useState<string[] | null>(null);

  useEffect(() => {
    HttpService.makeCallToBackend({
      path: `/user-groups/for-current-user`,
      successCallback: setUserGroups,
    });
  }, [setUserGroups]);

  const groupTableComponents = () => {
    if (!userGroups) {
      return null;
    }

    return userGroups.map((userGroup: string) => {
      const titleText = `This is a list of instances with tasks that were completed by the ${userGroup} group.`;
      const headerElement = (
        <h2 title={titleText} className="process-instance-table-header">
          Instances with tasks completed by <strong>{userGroup}</strong>
        </h2>
      );
      return (
        <ProcessInstanceListTable
          headerElement={headerElement}
          showLinkToReport
          filtersEnabled={false}
          paginationQueryParamPrefix="group_completed_instances"
          paginationClassName="with-large-bottom-margin"
          perPageOptions={[2, 5, 25]}
          reportIdentifier="system_report_completed_instances"
          showReports={false}
          textToShowIfEmpty="This group has no completed instances at this time."
          additionalReportFilters={[
            { field_name: 'user_group_identifier', field_value: userGroup },
          ]}
          showActionsColumn
        />
      );
    });
  };

  const startedByMeTitleText =
    'This is a list of instances you started that are now complete.';
  const startedByMeHeaderElement = (
    <h2 title={startedByMeTitleText} className="process-instance-table-header">
      Started by me
    </h2>
  );
  const withTasksCompletedByMeTitleText =
    'This is a list of instances where you have completed tasks.';
  const withTasksHeaderElement = (
    <h2
      title={withTasksCompletedByMeTitleText}
      className="process-instance-table-header"
    >
      Instances with tasks completed by me
    </h2>
  );

  return (
    <>
      <ProcessInstanceListTable
        headerElement={startedByMeHeaderElement}
        showLinkToReport
        filtersEnabled={false}
        paginationQueryParamPrefix="my_completed_instances"
        perPageOptions={[2, 5, 25]}
        reportIdentifier="system_report_completed_instances_initiated_by_me"
        showReports={false}
        textToShowIfEmpty="You have no completed instances at this time."
        paginationClassName="with-large-bottom-margin"
        autoReload
        showActionsColumn
      />
      <ProcessInstanceListTable
        headerElement={withTasksHeaderElement}
        showLinkToReport
        filtersEnabled={false}
        paginationQueryParamPrefix="my_completed_tasks"
        perPageOptions={[2, 5, 25]}
        reportIdentifier="system_report_completed_instances_with_tasks_completed_by_me"
        showReports={false}
        textToShowIfEmpty="You have no completed instances at this time."
        paginationClassName="with-large-bottom-margin"
        showActionsColumn
      />
      {groupTableComponents()}
    </>
  );
}
