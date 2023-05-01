import { useEffect, useState } from 'react';
import ProcessInstanceListTable from '../components/ProcessInstanceListTable';
import { slugifyString } from '../helpers';
import HttpService from '../services/HttpService';

export default function InProgressInstances() {
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
      const titleText = `This is a list of instances with tasks that are waiting for the ${userGroup} group.`;
      const headerElement = (
        <h2 title={titleText} className="process-instance-table-header">
          Instances with tasks waiting for <strong>{userGroup}</strong>
        </h2>
      );
      return (
        <ProcessInstanceListTable
          headerElement={headerElement}
          showLinkToReport
          filtersEnabled={false}
          paginationQueryParamPrefix={`waiting_for_${slugifyString(
            userGroup
          ).replace('-', '_')}`}
          paginationClassName="with-large-bottom-margin"
          perPageOptions={[2, 5, 25]}
          reportIdentifier="system_report_in_progress_instances_with_tasks"
          showReports={false}
          textToShowIfEmpty="This group has no instances waiting on it at this time."
          additionalReportFilters={[
            { field_name: 'user_group_identifier', field_value: userGroup },
          ]}
          canCompleteAllTasks
          showActionsColumn
          autoReload={false}
        />
      );
    });
  };

  const startedByMeTitleText =
    'This is a list of open instances that you started.';
  const startedByMeHeaderElement = (
    <h2 title={startedByMeTitleText} className="process-instance-table-header">
      Started by me
    </h2>
  );

  const waitingForMeTitleText =
    'This is a list of instances that have tasks that you can complete.';
  const waitingForMeHeaderElement = (
    <h2 title={waitingForMeTitleText} className="process-instance-table-header">
      Instances with tasks waiting for me
    </h2>
  );

  return (
    <>
      <ProcessInstanceListTable
        headerElement={startedByMeHeaderElement}
        filtersEnabled={false}
        paginationQueryParamPrefix="open_instances_started_by_me"
        perPageOptions={[2, 5, 25]}
        reportIdentifier="system_report_in_progress_instances_initiated_by_me"
        showReports={false}
        textToShowIfEmpty="There are no open instances you started at this time."
        paginationClassName="with-large-bottom-margin"
        showLinkToReport
        showActionsColumn
        autoReload={false}
      />
      <ProcessInstanceListTable
        headerElement={waitingForMeHeaderElement}
        showLinkToReport
        filtersEnabled={false}
        paginationQueryParamPrefix="waiting_for_me"
        perPageOptions={[2, 5, 25]}
        reportIdentifier="system_report_in_progress_instances_with_tasks_for_me"
        showReports={false}
        textToShowIfEmpty="There are no instances waiting on you at this time."
        paginationClassName="with-large-bottom-margin"
        canCompleteAllTasks
        showActionsColumn
        autoReload
      />
      {groupTableComponents()}
    </>
  );
}
