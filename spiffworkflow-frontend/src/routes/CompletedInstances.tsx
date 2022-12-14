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
          <h2>With tasks completed by group: {userGroup}</h2>
          <p className="data-table-description">
            This is a list of instances with tasks that were completed by the{' '}
            {userGroup} group.
          </p>
          <ProcessInstanceListTable
            filtersEnabled={false}
            paginationQueryParamPrefix="group_completed_instances"
            paginationClassName="with-large-bottom-margin"
            perPageOptions={[2, 5, 25]}
            reportIdentifier="system_report_completed_instances_with_tasks_completed_by_my_groups"
            showReports={false}
            textToShowIfEmpty="This group has no completed instances at this time."
            additionalParams={`user_group_identifier=${userGroup}`}
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
        reportIdentifier="system_report_completed_instances_initiated_by_me"
        showReports={false}
        textToShowIfEmpty="You have no completed instances at this time."
        paginationClassName="with-large-bottom-margin"
        autoReload
      />
      <h2>With tasks completed by me</h2>
      <p className="data-table-description">
        This is a list of instances where you have completed tasks.
      </p>
      <ProcessInstanceListTable
        filtersEnabled={false}
        paginationQueryParamPrefix="my_completed_tasks"
        perPageOptions={[2, 5, 25]}
        reportIdentifier="system_report_completed_instances_with_tasks_completed_by_me"
        showReports={false}
        textToShowIfEmpty="You have no completed instances at this time."
        paginationClassName="with-large-bottom-margin"
      />
      {groupTableComponents()}
    </>
  );
}
