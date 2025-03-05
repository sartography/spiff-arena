import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import {
  Box,
  Button,
  CircularProgress,
  Stack,
  Typography,
} from '@mui/material';

import { useDebouncedCallback } from 'use-debounce';
import HttpService from '../../services/HttpService';
import useAPIError from '../../hooks/UseApiError';
import {
  doNothing,
  modifyProcessIdentifierForPathParam,
  recursivelyChangeNullAndUndefined,
  renderElementsForArray,
  setPageTitle,
} from '../../helpers';
import {
  BasicTask,
  ElementForArray,
  ErrorForDisplay,
  EventDefinition,
  HotCrumbItem,
  Task,
} from '../../interfaces';
import CustomForm from '../../components/CustomForm';
import ProcessBreadcrumb from '../../components/ProcessBreadcrumb';
import InstructionsForEndUser from '../../components/InstructionsForEndUser';

export default function TaskShow() {
  const [basicTask, setBasicTask] = useState<BasicTask | null>(null);
  const [taskWithTaskData, setTaskWithTaskData] = useState<Task | null>(null);
  const [hotCrumbs, setHotCrumbs] = useState<HotCrumbItem[]>([]);

  const params = useParams();
  const navigate = useNavigate();
  const [formButtonsDisabled, setFormButtonsDisabled] = useState(false);

  const [taskData, setTaskData] = useState<any>(null);
  const [autosaveOnFormChanges, setAutosaveOnFormChanges] =
    useState<boolean>(true);
  const [atLeastOneTaskFetchHasError, setAtLeastOneTaskFetchHasError] =
    useState<boolean>(false);

  const { addError, removeError } = useAPIError();

  const addErrorCallback = useCallback((error: ErrorForDisplay) => {
    addError(error);
    // FIXME: not sure what to do about addError. adding it to this array causes the page to endlessly reload
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const navigateToInterstitial = useCallback(
    (myTask: BasicTask) => {
      navigate(
        `/process-instances/for-me/${modifyProcessIdentifierForPathParam(
          myTask.process_model_identifier,
        )}/${myTask.process_instance_id}/interstitial`,
      );
    },
    [navigate],
  );

  const processBasicTaskResult = useCallback(
    (result: BasicTask) => {
      setBasicTask(result);
      setPageTitle([result.name_for_display]);
      if (!result.can_complete) {
        if (result.process_model_uses_queued_execution) {
          navigate(
            `/process-instances/for-me/${modifyProcessIdentifierForPathParam(
              result.process_model_identifier,
            )}/${result.process_instance_id}/progress`,
          );
        } else {
          navigateToInterstitial(result);
        }
      }
      const hotCrumbList: HotCrumbItem[] = [
        ['Process Groups', '/process-groups'],
        {
          entityToExplode: result.process_model_identifier,
          entityType: 'process-model-id',
          linkLastItem: true,
          checkPermission: true,
        },
        [
          `Process Instance Id: ${result.process_instance_id}`,
          `/process-instances/for-me/${modifyProcessIdentifierForPathParam(
            result.process_model_identifier,
          )}/${result.process_instance_id}`,
        ],
        [`Task: ${result.name_for_display || result.id}`],
      ];
      setHotCrumbs(hotCrumbList);
    },
    [navigateToInterstitial, navigate],
  );

  useEffect(() => {
    const processTaskWithDataResult = (result: Task) => {
      setTaskWithTaskData(result);

      const taskDataToUse = result.saved_form_data || result.data;
      setTaskData(recursivelyChangeNullAndUndefined(taskDataToUse, undefined));
      setFormButtonsDisabled(false);
    };
    const handleTaskFetchError = (error: ErrorForDisplay) => {
      setAtLeastOneTaskFetchHasError(true);
      addErrorCallback(error);
    };

    HttpService.makeCallToBackend({
      path: `/tasks/${params.process_instance_id}/${params.task_guid}`,
      successCallback: processBasicTaskResult,
      failureCallback: handleTaskFetchError,
    });
    HttpService.makeCallToBackend({
      path: `/tasks/${params.process_instance_id}/${params.task_guid}?with_form_data=true`,
      successCallback: processTaskWithDataResult,
      failureCallback: handleTaskFetchError,
    });
  }, [
    params.task_guid,
    params.process_instance_id,
    processBasicTaskResult,
    addErrorCallback,
  ]);

  const autoSaveTaskData = (formData: any, successCallback?: Function) => {
    if (['ManualTask', 'Task'].includes(taskWithTaskData?.typename || '')) {
      return undefined;
    }
    let successCallbackToUse = successCallback;
    if (!successCallbackToUse) {
      successCallbackToUse = doNothing;
    }
    HttpService.makeCallToBackend({
      path: `/tasks/${params.process_instance_id}/${params.task_guid}/save-draft`,
      postBody: formData,
      httpMethod: 'POST',
      successCallback: successCallbackToUse,
    });
    return undefined;
  };

  const sendAutosaveEvent = (eventDetails?: any) => {
    if (!taskWithTaskData) {
      return;
    }
    const elementToDispath: any = document.getElementById(
      `hidden-form-for-autosave-${taskWithTaskData.guid}`,
    );
    if (elementToDispath) {
      elementToDispath.dispatchEvent(
        new CustomEvent('submit', {
          cancelable: true,
          bubbles: true,
          detail: eventDetails,
        }),
      );
    }
  };

  const addDebouncedTaskDataAutoSave = useDebouncedCallback(() => {
    if (autosaveOnFormChanges) {
      sendAutosaveEvent();
    }
  }, 500);

  const processSubmitResult = (result: any) => {
    removeError();
    if (result.ok) {
      navigate('/');
    } else if (result.process_instance_id) {
      if (result.can_complete) {
        navigate(`/tasks/${result.process_instance_id}/${result.id}`);
      } else if (result.process_model_uses_queued_execution) {
        navigate(
          `/process-instances/for-me/${modifyProcessIdentifierForPathParam(
            result.process_model_identifier,
          )}/${result.process_instance_id}/progress`,
        );
      } else {
        navigateToInterstitial(result);
      }
    } else {
      setFormButtonsDisabled(false);
      addError(result);
    }
  };

  const handleAutosaveFormSubmit = (formObject: any, event: any) => {
    const dataToSubmit = formObject?.formData;
    let successCallback = null;
    if (event.detail && 'successCallback' in event.detail) {
      successCallback = event.detail.successCallback;
    }
    autoSaveTaskData(
      recursivelyChangeNullAndUndefined(dataToSubmit, null),
      successCallback,
    );
  };

  const handleFormSubmit = (formObject: any, _event: any) => {
    if (formButtonsDisabled) {
      return;
    }

    const dataToSubmit = formObject?.formData;

    if (!dataToSubmit) {
      navigate(`/tasks`);
      return;
    }
    const queryParams = '';

    setFormButtonsDisabled(true);
    removeError();
    delete dataToSubmit.isManualTask;

    recursivelyChangeNullAndUndefined(dataToSubmit, null);

    HttpService.makeCallToBackend({
      path: `/tasks/${params.process_instance_id}/${params.task_guid}${queryParams}`,
      successCallback: processSubmitResult,
      failureCallback: (error: any) => {
        addError(error);
      },
      httpMethod: 'PUT',
      postBody: dataToSubmit,
    });
  };

  const handleSignalSubmit = (event: EventDefinition) => {
    if (formButtonsDisabled || !taskWithTaskData) {
      return;
    }
    setFormButtonsDisabled(true);
    HttpService.makeCallToBackend({
      path: `/tasks/${params.process_instance_id}/send-user-signal-event`,
      successCallback: processSubmitResult,
      failureCallback: (error: any) => {
        addError(error);
      },
      httpMethod: 'POST',
      postBody: event,
    });
  };

  const handleCloseButton = () => {
    setAutosaveOnFormChanges(false);
    setFormButtonsDisabled(true);
    const successCallback = () => navigate('/');
    sendAutosaveEvent({ successCallback });
  };

  const getSubmitButtonOptions = (formUiSchema: any) => {
    const uiOptionsString = 'ui:options';
    let submitButtonOptions = {};
    if ('ui:submitButtonOptions' in formUiSchema) {
      submitButtonOptions = formUiSchema['ui:submitButtonOptions'];
    }
    if (
      uiOptionsString in formUiSchema &&
      'submitButtonOptions' in formUiSchema[uiOptionsString]
    ) {
      submitButtonOptions = {
        ...submitButtonOptions,
        ...formUiSchema[uiOptionsString].submitButtonOptions,
      };
    }
    return submitButtonOptions;
  };

  const getSubmitButtonText = (formUiSchema: any) => {
    if (!taskWithTaskData) {
      return null;
    }
    const submitButtonOptions = getSubmitButtonOptions(formUiSchema);
    let submitButtonText = 'Submit';
    if ('submitText' in submitButtonOptions) {
      submitButtonText = submitButtonOptions.submitText as string;
    } else if (taskWithTaskData.typename === 'ManualTask') {
      submitButtonText = 'Continue';
    }
    return submitButtonText;
  };

  const formElement = () => {
    if (!taskWithTaskData) {
      return null;
    }

    let formUiSchema;
    let jsonSchema = taskWithTaskData.form_schema;
    let reactFragmentToHideSubmitButton = null;
    if (taskWithTaskData.typename !== 'UserTask') {
      jsonSchema = {
        type: 'object',
        required: [],
        properties: {
          isManualTask: {
            type: 'boolean',
            title: 'Is ManualTask',
            default: true,
          },
        },
      };
      formUiSchema = {
        isManualTask: {
          'ui:widget': 'hidden',
        },
      };
    } else if (taskWithTaskData.form_ui_schema) {
      formUiSchema = taskWithTaskData.form_ui_schema;
    }
    if (taskWithTaskData.state !== 'READY') {
      formUiSchema = Object.assign(formUiSchema || {}, {
        'ui:readonly': true,
      });

      reactFragmentToHideSubmitButton = <div />;
    }

    if (taskWithTaskData.state === 'READY') {
      const submitButtonText = getSubmitButtonText(formUiSchema);
      let closeButton = null;
      if (taskWithTaskData.typename === 'UserTask') {
        closeButton = (
          <Button
            id="close-button"
            onClick={handleCloseButton}
            disabled={formButtonsDisabled}
            title="Save data as draft and close the form."
            variant="contained"
            color="secondary"
          >
            Save and close
          </Button>
        );
      }
      reactFragmentToHideSubmitButton = (
        <Stack direction="row" spacing={2}>
          <Button
            type="submit"
            id="submit-button"
            disabled={formButtonsDisabled}
            variant="contained"
          >
            {submitButtonText}
          </Button>
          {closeButton}
          <>
            {taskWithTaskData.signal_buttons.map((signal) => (
              <Button
                name="signal.signal"
                disabled={formButtonsDisabled}
                onClick={() => handleSignalSubmit(signal.event)}
                variant="contained"
                color="secondary"
              >
                {signal.label}
              </Button>
            ))}
          </>
        </Stack>
      );
    }

    return (
      <Box className="limited-width-for-readability">
        <CustomForm
          id={`form-to-submit-${taskWithTaskData.guid}`}
          key={`form-to-submit-${taskWithTaskData.guid}`}
          disabled={formButtonsDisabled}
          formData={taskData}
          onChange={(obj: any) => {
            setTaskData(obj.formData);
            addDebouncedTaskDataAutoSave();
          }}
          onSubmit={handleFormSubmit}
          schema={jsonSchema}
          uiSchema={formUiSchema}
        >
          {reactFragmentToHideSubmitButton}
        </CustomForm>
        <CustomForm
          id={`hidden-form-for-autosave-${taskWithTaskData.guid}`}
          key={`hidden-form-for-autosave-${taskWithTaskData.guid}`}
          className="hidden-form-for-autosave"
          formData={taskData}
          onSubmit={handleAutosaveFormSubmit}
          schema={jsonSchema}
          uiSchema={formUiSchema}
          noValidate
        />
      </Box>
    );
  };

  const getLoadingIcon = () => {
    const style = { margin: '50px' };
    return <CircularProgress style={style} />;
  };

  const pageElements: ElementForArray[] = [];
  if (basicTask) {
    let statusString = '';
    if (basicTask.state !== 'READY') {
      statusString = ` ${basicTask.state}`;
    }

    pageElements.push({
      key: 'process-breadcrumb',
      component: <ProcessBreadcrumb hotCrumbs={hotCrumbs} />,
    });
    pageElements.push({
      key: 'task-name',
      component: (
        <Typography variant="h3">
          Task: {basicTask.name_for_display} (
          {basicTask.process_model_display_name}){statusString}
        </Typography>
      ),
    });
  }

  if (basicTask && taskData) {
    pageElements.push({
      key: 'instructions-for-end-user',
      component: (
        <InstructionsForEndUser
          task={taskWithTaskData}
          className="with-bottom-margin"
        />
      ),
    });
    pageElements.push({ key: 'main-form', component: formElement() });
  } else if (!atLeastOneTaskFetchHasError) {
    pageElements.push({ key: 'loading-icon', component: getLoadingIcon() });
  }

  return (
    <Box sx={{ my: 4, mx: 8 }}>{renderElementsForArray(pageElements)}</Box>
  );
}
