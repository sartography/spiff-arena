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
      const titleText = `Esta é uma lista de processos com tarefas que estão aguardando pelo grupo ${userGroup}.`;
      const headerElement = {
        tooltip_text: titleText,
        text: `Aguardando por **${userGroup}**`,
      };
      const identifierForTable = `waiting-for-${slugifyString(userGroup)}`;
      return (
        <ProcessInstanceListTable
          additionalReportFilters={[
            { field_name: 'user_group_identifier', field_value: userGroup },
          ]}
          autoReload
          header={headerElement}
          paginationClassName="with-large-bottom-margin"
          paginationQueryParamPrefix={identifierForTable.replace('-', '_')}
          perPageOptions={[2, 5, 25]}
          reportIdentifier="system_report_in_progress_instances_with_tasks"
          showActionsColumn
          showLinkToReport
          tableHtmlId={identifierForTable}
          textToShowIfEmpty="Este grupo não tem processos aguardando neste momento."
        />
      );
    });
  };

  const startedByMeTitleText =
    'Esta é uma lista de processos em andamento que você iniciou.';
  const startedByMeHeaderElement = {
    tooltip_text: startedByMeTitleText,
    text: 'Iniciados por mim',
  };

  const waitingForMeTitleText =
    'Esta é uma lista de processos que têm tarefas que você pode completar.';
  const waitingForMeHeaderElement = {
    tooltip_text: waitingForMeTitleText,
    text: 'Aguardando por mim',
  };

  return (
    <>
      <ProcessInstanceListTable
        autoReload
        header={startedByMeHeaderElement}
        paginationClassName="with-large-bottom-margin"
        paginationQueryParamPrefix="open_instances_started_by_me"
        perPageOptions={[2, 5, 25]}
        reportIdentifier="system_report_in_progress_instances_initiated_by_me"
        showActionsColumn
        showLinkToReport
        tableHtmlId="open-instances-started-by-me"
        textToShowIfEmpty="No momento, não há processos em andamento que você iniciou."
      />
      <ProcessInstanceListTable
        autoReload
        header={waitingForMeHeaderElement}
        paginationClassName="with-large-bottom-margin"
        paginationQueryParamPrefix="waiting_for_me"
        perPageOptions={[2, 5, 25]}
        reportIdentifier="system_report_in_progress_instances_with_tasks_for_me"
        showActionsColumn
        showLinkToReport
        tableHtmlId="waiting-for-me"
        textToShowIfEmpty="No momento, não há processos aguardando sua ação."
      />
      {groupTableComponents()}
    </>
  );
}
