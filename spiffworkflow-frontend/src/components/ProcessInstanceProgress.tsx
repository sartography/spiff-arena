import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loading } from '@carbon/react';

import {
  ErrorForDisplay,
  ProcessInstanceProgressResponse,
  ProcessInstanceTask,
  TaskInstructionForEndUser,
} from '../interfaces';
import { HUMAN_TASK_TYPES, refreshAtInterval } from '../helpers';
import HttpService from '../services/HttpService';
import DateAndTimeService from '../services/DateAndTimeService';
import InstructionsForEndUser from './InstructionsForEndUser';
import {
  ErrorDisplayStateless,
  errorForDisplayFromProcessInstanceErrorDetail,
} from './ErrorDisplay';

type OwnProps = {
  processInstanceId: number;
  processInstanceShowPageUrl: string;
  smallSpinner?: boolean;
};

export default function ProcessInstanceProgress({
  processInstanceId,
  processInstanceShowPageUrl,
  smallSpinner = false,
}: OwnProps) {
  const [currentPageError, setCurrentPageError] =
    useState<ErrorForDisplay | null>(null);
  const [taskInstructionForEndUserList, setTaskInstructionForEndUserList] =
    useState<TaskInstructionForEndUser[]>([]);
  const [errorHasOccurred, setErrorHasOccurred] = useState<boolean>(false);

  const navigate = useNavigate();

  const shouldRedirectToTask = useCallback(
    (myTask: ProcessInstanceTask): boolean => {
      return (
        myTask && myTask.can_complete && HUMAN_TASK_TYPES.includes(myTask.type)
      );
    },
    [],
  );

  // Useful to stop refreshing if an api call gets an error
  // since those errors can make the page unusable in any way
  const clearRefreshRef = useRef<any>(null);
  const stopRefreshing = useCallback((error: any) => {
    if (clearRefreshRef.current) {
      clearRefreshRef.current();
    }
    if (error) {
      setCurrentPageError(error);
      setErrorHasOccurred(true);
    }
  }, []);

  useEffect(() => {
    const processResult = (result: ProcessInstanceProgressResponse) => {
      if (result.task && shouldRedirectToTask(result.task)) {
        // if task you can complete, go there
        navigate(`/tasks/${result.task.process_instance_id}/${result.task.id}`);
      } else if (result.error_details && result.process_instance_event) {
        const error = errorForDisplayFromProcessInstanceErrorDetail(
          result.process_instance_event,
          result.error_details,
        );
        stopRefreshing(error);
      } else if (result.process_instance) {
        // there is nothing super exciting happening right now. go to process instance.
        if (
          result.process_instance.actions &&
          'read' in result.process_instance.actions
        ) {
          navigate(processInstanceShowPageUrl);
        } else {
          navigate('/');
        }
      }

      // otherwise render instructions
      setTaskInstructionForEndUserList((prevInstructions) => [
        ...result.instructions,
        ...prevInstructions,
      ]);
    };

    const checkProgress = () => {
      HttpService.makeCallToBackend({
        path: `/tasks/progress/${processInstanceId}`,
        successCallback: processResult,
        httpMethod: 'GET',
        failureCallback: stopRefreshing,
      });
    };
    clearRefreshRef.current = refreshAtInterval(
      // 15,
      1,
      DateAndTimeService.REFRESH_TIMEOUT_SECONDS,
      checkProgress,
    );
    return clearRefreshRef.current;
  }, [
    shouldRedirectToTask,
    navigate,
    processInstanceId,
    processInstanceShowPageUrl,
    stopRefreshing,
  ]);

  const getLoadingIcon = () => {
    if (errorHasOccurred) {
      return null;
    }
    let style = { margin: '50px 0 50px 50px' };
    if (smallSpinner) {
      style = { margin: '2x 5px 2px 2px' };
    }
    return (
      <Loading
        description="Active loading indicator"
        withOverlay={false}
        small={smallSpinner}
        style={style}
      />
    );
  };

  const userMessage = (
    taskInstructionForEndUser: TaskInstructionForEndUser,
  ) => {
    return (
      <InstructionsForEndUser
        taskInstructionForEndUser={taskInstructionForEndUser}
        defaultMessage="There are no instructions or information for this task."
      />
    );
  };

  const errorDisplayArea = () => {
    if (currentPageError) {
      return (
        <>
          {ErrorDisplayStateless(currentPageError)}
          <p>
            Go to <a href={processInstanceShowPageUrl}>Process Instance</a>
          </p>
        </>
      );
    }
    return null;
  };

  if (taskInstructionForEndUserList) {
    const className = (index: number) => {
      if (taskInstructionForEndUserList.length === 1) {
        return 'user_instructions';
      }
      return index < 4 ? `user_instructions_${index}` : `user_instructions_4`;
    };
    return (
      <div>
        {errorDisplayArea()}
        {getLoadingIcon()}
        {taskInstructionForEndUserList.map((instruction, index) => {
          return (
            <div className={className(index)}>{userMessage(instruction)}</div>
          );
        })}
      </div>
    );
  }

  return (
    <div>
      {errorDisplayArea()}
      {getLoadingIcon()}
    </div>
  );
}
