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
      return (
        <>
          <h2>Tasks completed by {userGroup} group</h2>
          <p className="data-table-description">
            This is a list of instances with tasks that were completed by the{' '}
            {userGroup} group.
          </p>
          <ProcessInstanceListTable
            filtersEnabled={false}
            paginationQueryParamPrefix="group_completed_tasks"
            paginationClassName="with-large-bottom-margin"
            perPageOptions={[2, 5, 25]}
            reportIdentifier="system_report_instances_with_tasks_completed_by_my_groups"
            showReports={false}
            textToShowIfEmpty="Your group has no completed tasks at this time."
            additionalParams={`group_identifier=${userGroup}`}
          />
        </>
      );
    });
  };

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
      {groupTableComponents()}
    </>
  );
}
