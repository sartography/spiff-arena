import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { Grid, Column, Button, ButtonSet, Loading } from '@carbon/react';

import { useDebouncedCallback } from 'use-debounce';
import HttpService from '../services/HttpService';
import useAPIError from '../hooks/UseApiError';
import {
  doNothing,
  modifyProcessIdentifierForPathParam,
  recursivelyChangeNullAndUndefined,
  renderElementsForArray,
  setPageTitle,
} from '../helpers';
import {
  BasicTask,
  ElementForArray,
  ErrorForDisplay,
  EventDefinition,
  HotCrumbItem,
  Task,
} from '../interfaces';
import CustomForm from '../components/CustomForm';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import InstructionsForEndUser from '../components/InstructionsForEndUser';

export default function TaskShow() {
  // get a basic task which doesn't get the form data so we can load
  // the basic form and structure of the page without waiting for form data.
  // this was mainly to help with loading form data with large files attached to it
  const [basicTask, setBasicTask] = useState<BasicTask | null>(null);
  const [taskWithTaskData, setTaskWithTaskData] = useState<Task | null>(null);

  // put this in a state so ProcessBreadCrumb does not attempt to re-render
  // since javascript cannot tell if an array or object has changed
  // but react states can. If we simply initialize a ProcessBreadCrumb when
  // this parent component renders, we get a request to process model show
  // every time someone types a character into a user task form (because we change ANY
  // state. in this case, setTaskData).
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

  // if a user can complete a task then the for-me page should
  // always work for them so use that since it will work in all cases
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

      // convert null back to undefined so rjsf doesn't attempt to incorrectly validate them
      const taskDataToUse = result.saved_form_data || result.data;
      setTaskData(recursivelyChangeNullAndUndefined(taskDataToUse, undefined));
      setFormButtonsDisabled(false);
    };
    const handleTaskFetchError = (error: ErrorForDisplay) => {
      setAtLeastOneTaskFetchHasError(true);
      addErrorCallback(error);
    };

    HttpService.makeCallToBackend({
      path: `/tasks/${params.process_instance_id}/${params.task_id}`,
      successCallback: processBasicTaskResult,
      failureCallback: handleTaskFetchError,
    });
    HttpService.makeCallToBackend({
      path: `/tasks/${params.process_instance_id}/${params.task_id}?with_form_data=true`,
      successCallback: processTaskWithDataResult,
      failureCallback: handleTaskFetchError,
    });
  }, [
    params.task_id,
    params.process_instance_id,
    processBasicTaskResult,
    addErrorCallback,
  ]);

  // Before we auto-saved form data, we remembered what data was in the form, and then created a synthetic submit event
  // in order to implement a "Save and close" button. That button no longer saves (since we have auto-save), but the crazy
  // frontend code to support that Save and close button is here, in case we need to reference that someday:
  //   https://github.com/sartography/spiff-arena/blob/182f56a1ad23ce780e8f5b0ed00efac3e6ad117b/spiffworkflow-frontend/src/routes/TaskShow.tsx#L329
  const autoSaveTaskData = (formData: any, successCallback?: Function) => {
    // save-draft gets called when a manual task form loads but there's no data to save so don't do it
    if (['ManualTask', 'Task'].includes(taskWithTaskData?.typename || '')) {
      return undefined;
    }
    let successCallbackToUse = successCallback;
    if (!successCallbackToUse) {
      successCallbackToUse = doNothing;
    }
    HttpService.makeCallToBackend({
      path: `/tasks/${params.process_instance_id}/${params.task_id}/save-draft`,
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

  const addDebouncedTaskDataAutoSave = useDebouncedCallback(
    () => {
      if (autosaveOnFormChanges) {
        sendAutosaveEvent();
      }
    },
    // delay in ms
    500,
  );

  const processSubmitResult = (result: any) => {
    removeError();
    if (result.ok) {
      navigate(`/tasks`);
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

    // NOTE: rjsf sets blanks values to undefined and JSON.stringify removes keys with undefined values
    // so we convert undefined values to null recursively so that we can unset values in form fields
    recursivelyChangeNullAndUndefined(dataToSubmit, null);

    HttpService.makeCallToBackend({
      path: `/tasks/${params.process_instance_id}/${params.task_id}${queryParams}`,
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
    const successCallback = () => navigate(`/tasks`);
    sendAutosaveEvent({ successCallback });
  };

  // we had to duplicate this logic because we pass chlidren to the Form.
  // we pass children to the form because of additional submit buttons on the form for signals, and we
  // probably want these to be styled next to the default button.
  // if we remove the children prop from the Form, the submit button text works perfectly per the
  // docs at https://rjsf-team.github.io/react-jsonschema-form/docs/api-reference/uiSchema
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

      // It doesn't seem as if Form allows for removing the default submit button
      // so passing a blank fragment or children seem to do it though
      //
      // from: https://github.com/rjsf-team/react-jsonschema-form/issues/1602
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
            kind="primary"
            title="Save data as draft and close the form."
          >
            Save and close
          </Button>
        );
      }
      reactFragmentToHideSubmitButton = (
        <ButtonSet>
          <Button
            type="submit"
            id="submit-button"
            disabled={formButtonsDisabled}
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
              >
                {signal.label}
              </Button>
            ))}
          </>
        </ButtonSet>
      );
    }

    // we are using two forms here so we can have one that validates data and one that does not.
    // this allows us to autosave form data without extra attributes and without validations
    // but still requires validations when the user submits the form that they can edit.
    return (
      <Grid fullWidth condensed className="megacondensed">
        <Column sm={4} md={5} lg={8}>
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
            restrictedWidth
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
            restrictedWidth
          />
        </Column>
      </Grid>
    );
  };

  const getLoadingIcon = () => {
    const style = { margin: '50px 0 50px 50px' };
    return (
      <Loading
        description="Active loading indicator"
        withOverlay={false}
        style={style}
      />
    );
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
        <h3>
          Task: {basicTask.name_for_display} (
          {basicTask.process_model_display_name}){statusString}
        </h3>
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

  return <>{renderElementsForArray(pageElements)}</>;
}
