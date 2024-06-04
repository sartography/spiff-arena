import { useEffect, useState } from 'react';
import ProcessInstanceListTable from '../components/ProcessInstanceListTable';
import { slugifyString } from '../helpers';
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
      const headerElement = {
        tooltip_text: titleText,
        text: `Instances with tasks completed by **${userGroup}**`,
      };
      const identifierForTable = `completed-by-group-${slugifyString(
        userGroup,
      )}`;
      return (
        <ProcessInstanceListTable
          additionalReportFilters={[
            { field_name: 'user_group_identifier', field_value: userGroup },
          ]}
          header={headerElement}
          paginationClassName="with-large-bottom-margin"
          paginationQueryParamPrefix="group_completed_instances"
          perPageOptions={[2, 5, 25]}
          reportIdentifier="system_report_completed_instances"
          showActionsColumn
          showLinkToReport
          tableHtmlId={identifierForTable}
          textToShowIfEmpty="This group has no completed instances at this time."
        />
      );
    });
  };

  const startedByMeTitleText =
    'This is a list of instances you started that are now complete.';
  const startedByMeHeaderElement = {
    tooltip_text: startedByMeTitleText,
    text: 'Started by me',
  };
  const withTasksCompletedByMeTitleText =
    'This is a list of instances where you have completed tasks.';
  const withTasksHeaderElement = {
    tooltip_text: withTasksCompletedByMeTitleText,
    text: 'Instances with tasks completed by me',
  };

  return (
    <>
      <ProcessInstanceListTable
        header={startedByMeHeaderElement}
        paginationClassName="with-large-bottom-margin"
        paginationQueryParamPrefix="my_completed_instances"
        perPageOptions={[2, 5, 25]}
        reportIdentifier="system_report_completed_instances_initiated_by_me"
        showActionsColumn
        showLinkToReport
        tableHtmlId="my-completed-instances"
        textToShowIfEmpty="You have no completed instances at this time."
      />
      <ProcessInstanceListTable
        header={withTasksHeaderElement}
        paginationClassName="with-large-bottom-margin"
        paginationQueryParamPrefix="my_completed_tasks"
        perPageOptions={[2, 5, 25]}
        reportIdentifier="system_report_completed_instances_with_tasks_completed_by_me"
        showActionsColumn
        showLinkToReport
        tableHtmlId="with-tasks-completed-by-me"
        textToShowIfEmpty="You have no completed instances at this time."
      />
      {groupTableComponents()}
    </>
  );
}
