import React, { useEffect, useState } from 'react';
import { InlineNotification } from '@carbon/react';

import InstructionsForEndUser from './InstructionsForEndUser';
import { ProcessInstance, ProcessInstanceTask } from '../interfaces';
import { HUMAN_TASK_TYPES } from '../helpers';
import HttpService from '../services/HttpService';

type OwnProps = {
  processInstance: ProcessInstance;
};

export default function ProcessInstanceCurrentTaskInfo({
  processInstance,
}: OwnProps) {
  const [taskResult, setTaskResult] = useState<any>(null);
  const [task, setTask] = useState<ProcessInstanceTask | null>(null);

  useEffect(() => {
    const processTaskResult = (result: any) => {
      setTaskResult(result);
      setTask(result.task);
    };
    HttpService.makeCallToBackend({
      path: `/tasks/${processInstance.id}/instruction`,
      successCallback: processTaskResult,
      failureCallback: (error: any) => console.error(error.message),
    });
  }, [processInstance]);

  const inlineMessage = (
    title: string,
    subtitle: string,
    kind: string = 'info',
  ) => {
    return (
      <div>
        <InlineNotification
          kind={kind}
          subtitle={subtitle}
          title={title}
          lowContrast
        />
      </div>
    );
  };

  const taskUserMessage = () => {
    if (!task) {
      return null;
    }

    if (!task.can_complete && HUMAN_TASK_TYPES.includes(task.type)) {
      let message = 'Esta próxima atividade é atribuída a uma pessoa ou equipe diferente.'
      if (task.assigned_user_group_identifier) {
        message = `Esta próxima atividade está atribuída ao grupo: ${task.assigned_user_group_identifier}.`;
      } else if (task.potential_owner_usernames) {
        let potentialOwnerArray = task.potential_owner_usernames.split(',');
        if (potentialOwnerArray.length > 2) {
          potentialOwnerArray = potentialOwnerArray.slice(0, 2).concat(['...']);
        }
        message = `Esta próxima atividade está atribuída ao(s) usuário(s): ${potentialOwnerArray.join(
          ', '
        )}.`;
      }

      return inlineMessage(
        '',
        `${message} Não há nenhuma ação para você tomar neste momento.`
      );
    }
    if (task && task.can_complete && HUMAN_TASK_TYPES.includes(task.type)) {
      return null;
    }
    return (
      <div>
        <InstructionsForEndUser task={task} allowCollapse />
      </div>
    );
  };

  const userMessage = () => {
    if (!processInstance) {
      return null;
    }
    if (['terminated', 'suspended'].includes(processInstance.status)) {
      return inlineMessage(
        `Processo ${processInstance.status}`,
        `Esta tarefa do processo foi ${processInstance.status} por um administrador. Por favor, entre em contato com eles para obter mais informações.`,
        'warning'
      );
    }
    if (processInstance.status === 'error') {
      let errMessage = `Esta tarefa do processo encontrou um erro inesperado e não pode continuar. Por favor, entre em contato com um administrador para mais informações e próximos passos.`;
      if (task && task.error_message) {
        errMessage = ` ${errMessage.concat(task.error_message)}`;
      }
      return inlineMessage(`Erro no Processo`, errMessage, 'error');
    }

    if (task) {
      return taskUserMessage();
    }
    const defaultMsg =
    'Não há instruções ou informações adicionais para este processo.';  
    return inlineMessage(`Erro no Processo`, defaultMsg, 'info');
  };

  if (processInstance && taskResult) {
    return <div className="user_instructions">{userMessage()}</div>;
  }

  return null;
}
