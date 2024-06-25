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
      const titleText = `Esta é uma lista de processos com instâncias que foram concluídas pelo grupo ${userGroup}.`;
      const headerElement = {
        tooltip_text: titleText,
        text: `Processos com instâncias concluídas pelo grupo **${userGroup}**`,
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
          perPageOptions={[50, 25, 10, 5]}
          reportIdentifier="system_report_completed_instances"
          showActionsColumn
          showLinkToReport
          tableHtmlId={identifierForTable}
          textToShowIfEmpty="Este grupo não possui processos concluídos neste momento."
        />
      );
    });
  };

  const startedByMeTitleText =
    'Esta é uma lista de processos que você iniciou e que agora estão concluídos.';
  const startedByMeHeaderElement = {
    tooltip_text: startedByMeTitleText,
    text: 'Iniciados por mim',
  };
  const withTasksCompletedByMeTitleText =
    'Esta é uma lista de processos onde você completou tarefas.';
  const withTasksHeaderElement = {
    tooltip_text: withTasksCompletedByMeTitleText,
    text: 'Processos com tarefas concluídas por mim',
  };

  return (
    <>
      <ProcessInstanceListTable
        header={startedByMeHeaderElement}
        paginationClassName="with-large-bottom-margin"
        paginationQueryParamPrefix="my_completed_instances"
        perPageOptions={[50, 25, 10, 5]}
        reportIdentifier="system_report_completed_instances_initiated_by_me"
        showActionsColumn
        showLinkToReport
        tableHtmlId="my-completed-instances"
        textToShowIfEmpty="No momento, você não possui processos concluídos."
      />
      <ProcessInstanceListTable
        header={withTasksHeaderElement}
        paginationClassName="with-large-bottom-margin"
        paginationQueryParamPrefix="my_completed_tasks"
        perPageOptions={[50, 25, 10, 5]}
        reportIdentifier="system_report_completed_instances_with_tasks_completed_by_me"
        showActionsColumn
        showLinkToReport
        tableHtmlId="with-tasks-completed-by-me"
        textToShowIfEmpty="No momento, você não possui processos concluídos."
      />
      {groupTableComponents()}
    </>
  );
}
