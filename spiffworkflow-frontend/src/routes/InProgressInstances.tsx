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
      const headerElement = {
        tooltip_text: titleText,
        text: `Waiting for <strong>${userGroup}</strong>`,
      };
      const identifierForTable = `waiting-for-${slugifyString(userGroup)}`;
      return (
        <ProcessInstanceListTable
          header={headerElement}
          tableHtmlId={identifierForTable}
          showLinkToReport
          filtersEnabled={false}
          paginationQueryParamPrefix={identifierForTable.replace('-', '_')}
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
          autoReload
        />
      );
    });
  };

  const startedByMeTitleText =
    'This is a list of open instances that you started.';
  const startedByMeHeaderElement = {
    tooltip_text: startedByMeTitleText,
    text: 'Started by me',
  };

  const waitingForMeTitleText =
    'This is a list of instances that have tasks that you can complete.';
  const waitingForMeHeaderElement = {
    tooltip_text: waitingForMeTitleText,
    text: 'Waiting for me',
  };

  return (
    <>
      <ProcessInstanceListTable
        header={startedByMeHeaderElement}
        tableHtmlId="open-instances-started-by-me"
        filtersEnabled={false}
        paginationQueryParamPrefix="open_instances_started_by_me"
        perPageOptions={[2, 5, 25]}
        reportIdentifier="system_report_in_progress_instances_initiated_by_me"
        showReports={false}
        textToShowIfEmpty="There are no open instances you started at this time."
        paginationClassName="with-large-bottom-margin"
        showLinkToReport
        showActionsColumn
        autoReload
      />
      <ProcessInstanceListTable
        header={waitingForMeHeaderElement}
        tableHtmlId="waiting-for-me"
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
