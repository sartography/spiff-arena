import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import validator from '@rjsf/validator-ajv8';

import {
  TabList,
  Tab,
  Tabs,
  Grid,
  Column,
  Button,
  ButtonSet,
} from '@carbon/react';

import { useDebouncedCallback } from 'use-debounce';
import { Form } from '../rjsf/carbon_theme';
import HttpService from '../services/HttpService';
import useAPIError from '../hooks/UseApiError';
import {
  doNothing,
  modifyProcessIdentifierForPathParam,
  recursivelyChangeNullAndUndefined,
} from '../helpers';
import { ErrorForDisplay, EventDefinition, Task } from '../interfaces';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import InstructionsForEndUser from '../components/InstructionsForEndUser';
import TypeaheadWidget from '../rjsf/custom_widgets/TypeaheadWidget/TypeaheadWidget';
import DateRangePickerWidget from '../rjsf/custom_widgets/DateRangePicker/DateRangePickerWidget';
import { DATE_RANGE_DELIMITER } from '../config';

export default function TaskShow() {
  const [task, setTask] = useState<Task | null>(null);
  const [userTasks] = useState(null);
  const params = useParams();
  const navigate = useNavigate();
  const [formButtonsDisabled, setFormButtonsDisabled] = useState(false);

  const [taskData, setTaskData] = useState<any>(null);
  const [autosaveOnFormChanges, setAutosaveOnFormChanges] =
    useState<boolean>(true);

  const { addError, removeError } = useAPIError();

  const rjsfWidgets = {
    typeahead: TypeaheadWidget,
    'date-range': DateRangePickerWidget,
  };

  // if a user can complete a task then the for-me page should
  // always work for them so use that since it will work in all cases
  const navigateToInterstitial = (myTask: Task) => {
    navigate(
      `/admin/process-instances/for-me/${modifyProcessIdentifierForPathParam(
        myTask.process_model_identifier
      )}/${myTask.process_instance_id}/interstitial`
    );
  };

  useEffect(() => {
    const processResult = (result: Task) => {
      setTask(result);

      // convert null back to undefined so rjsf doesn't attempt to incorrectly validate them
      const taskDataToUse = result.saved_form_data || result.data;
      setTaskData(recursivelyChangeNullAndUndefined(taskDataToUse, undefined));
      setFormButtonsDisabled(false);
      if (!result.can_complete) {
        navigateToInterstitial(result);
      }
    };
    HttpService.makeCallToBackend({
      path: `/tasks/${params.process_instance_id}/${params.task_id}`,
      successCallback: processResult,
      failureCallback: addError,
    });
    // FIXME: not sure what to do about addError. adding it to this array causes the page to endlessly reload
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params]);

  const handleAutoSaveError = (error: ErrorForDisplay) => {
    if (
      error.error_code &&
      error.error_code === 'process_instance_not_runnable'
    ) {
      return undefined;
    }
    addError(error);
    return undefined;
  };

  // Before we auto-saved form data, we remembered what data was in the form, and then created a synthetic submit event
  // in order to implement a "Save and close" button. That button no longer saves (since we have auto-save), but the crazy
  // frontend code to support that Save and close button is here, in case we need to reference that someday:
  //   https://github.com/sartography/spiff-arena/blob/182f56a1ad23ce780e8f5b0ed00efac3e6ad117b/spiffworkflow-frontend/src/routes/TaskShow.tsx#L329
  const autoSaveTaskData = (formData: any, successCallback?: Function) => {
    // save-draft gets called when a manual task form loads but there's no data to save so don't do it
    if (task?.typename === 'ManualTask') {
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
      failureCallback: handleAutoSaveError,
    });
    return undefined;
  };

  const sendAutosaveEvent = (eventDetails?: any) => {
    (document.getElementById('hidden-form-for-autosave') as any).dispatchEvent(
      new CustomEvent('submit', {
        cancelable: true,
        bubbles: true,
        detail: eventDetails,
      })
    );
  };

  const addDebouncedTaskDataAutoSave = useDebouncedCallback(
    () => {
      if (autosaveOnFormChanges) {
        sendAutosaveEvent();
      }
    },
    // delay in ms
    500
  );

  const processSubmitResult = (result: any) => {
    removeError();
    if (result.ok) {
      navigate(`/tasks`);
    } else if (result.process_instance_id) {
      if (result.can_complete) {
        navigate(`/tasks/${result.process_instance_id}/${result.id}`);
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
      successCallback
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
    if (formButtonsDisabled || !task) {
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

  const buildTaskNavigation = () => {
    let userTasksElement;
    let selectedTabIndex = 0;
    if (userTasks) {
      userTasksElement = (userTasks as any).map(function getUserTasksElement(
        userTask: any,
        index: number
      ) {
        const taskUrl = `/tasks/${params.process_instance_id}/${userTask.id}`;
        if (userTask.id === params.task_id) {
          selectedTabIndex = index;
          return <Tab selected>{userTask.name_for_display}</Tab>;
        }
        if (userTask.state === 'COMPLETED') {
          return (
            <Tab
              onClick={() => navigate(taskUrl)}
              data-qa={`form-nav-${userTask.name}`}
            >
              {userTask.name_for_display}
            </Tab>
          );
        }
        if (userTask.state === 'FUTURE') {
          return <Tab formButtonsDisabled>{userTask.name_for_display}</Tab>;
        }
        if (userTask.state === 'READY') {
          return (
            <Tab
              onClick={() => navigate(taskUrl)}
              data-qa={`form-nav-${userTask.name}`}
            >
              {userTask.name_for_display}
            </Tab>
          );
        }
        return null;
      });
      return (
        <Tabs
          title="Steps in this process instance involving people"
          selectedIndex={selectedTabIndex}
        >
          <TabList aria-label="List of tabs" contained>
            {userTasksElement}
          </TabList>
        </Tabs>
      );
    }
    return null;
  };

  const formatDateString = (dateString?: string) => {
    let dateObject = new Date();
    if (dateString) {
      dateObject = new Date(dateString);
    }
    return dateObject.toISOString().split('T')[0];
  };

  const checkFieldComparisons = (
    formData: any,
    propertyKey: string,
    minimumDateCheck: string,
    formattedDateString: string,
    errors: any,
    jsonSchema: any
  ) => {
    const fieldIdentifierToCompareWith = minimumDateCheck.replace(
      /^field:/,
      ''
    );
    if (fieldIdentifierToCompareWith in formData) {
      const dateToCompareWith = formData[fieldIdentifierToCompareWith];
      if (dateToCompareWith) {
        const dateStringToCompareWith = formatDateString(dateToCompareWith);
        if (dateStringToCompareWith > formattedDateString) {
          let fieldToCompareWithTitle = fieldIdentifierToCompareWith;
          if (
            fieldIdentifierToCompareWith in jsonSchema.properties &&
            jsonSchema.properties[fieldIdentifierToCompareWith].title
          ) {
            fieldToCompareWithTitle =
              jsonSchema.properties[fieldIdentifierToCompareWith].title;
          }
          errors[propertyKey].addError(
            `must be equal to or greater than '${fieldToCompareWithTitle}'`
          );
        }
      } else {
        errors[propertyKey].addError(
          `was supposed to be compared against '${fieldIdentifierToCompareWith}' but that field did not have a value`
        );
      }
    } else {
      errors[propertyKey].addError(
        `was supposed to be compared against '${fieldIdentifierToCompareWith}' but it either doesn't have a value or does not exist`
      );
    }
  };

  const checkMinimumDate = (
    formData: any,
    propertyKey: string,
    propertyMetadata: any,
    errors: any,
    jsonSchema: any
  ) => {
    let dateString = formData[propertyKey];
    if (dateString) {
      if (typeof dateString === 'string') {
        // in the case of date ranges, just take the start date and check that
        [dateString] = dateString.split(DATE_RANGE_DELIMITER);
      }
      const formattedDateString = formatDateString(dateString);
      const minimumDateChecks = propertyMetadata.minimumDate.split(',');
      minimumDateChecks.forEach((mdc: string) => {
        if (mdc === 'today') {
          const dateTodayString = formatDateString();
          if (dateTodayString > formattedDateString) {
            errors[propertyKey].addError('must be today or after');
          }
        } else if (mdc.startsWith('field:')) {
          checkFieldComparisons(
            formData,
            propertyKey,
            mdc,
            formattedDateString,
            errors,
            jsonSchema
          );
        }
      });
    }
  };

  const getFieldsWithDateValidations = (
    jsonSchema: any,
    formData: any,
    errors: any
    // eslint-disable-next-line sonarjs/cognitive-complexity
  ) => {
    // if the jsonSchema has an items attribute then assume the element itself
    // doesn't have a custom validation but it's children could so use that
    const jsonSchemaToUse =
      'items' in jsonSchema ? jsonSchema.items : jsonSchema;

    if ('properties' in jsonSchemaToUse) {
      Object.keys(jsonSchemaToUse.properties).forEach((propertyKey: string) => {
        const propertyMetadata = jsonSchemaToUse.properties[propertyKey];
        if ('minimumDate' in propertyMetadata) {
          checkMinimumDate(
            formData,
            propertyKey,
            propertyMetadata,
            errors,
            jsonSchemaToUse
          );
        }

        // recurse through all nested properties as well
        let formDataToSend = formData[propertyKey];
        if (formDataToSend) {
          if (formDataToSend.constructor.name !== 'Array') {
            formDataToSend = [formDataToSend];
          }
          formDataToSend.forEach((item: any, index: number) => {
            let errorsToSend = errors[propertyKey];
            if (index in errorsToSend) {
              errorsToSend = errorsToSend[index];
            }
            getFieldsWithDateValidations(propertyMetadata, item, errorsToSend);
          });
        }
      });
    }
    return errors;
  };

  const handleCloseButton = () => {
    setAutosaveOnFormChanges(false);
    setFormButtonsDisabled(true);
    const successCallback = () => navigate(`/tasks`);
    sendAutosaveEvent({ successCallback });
  };

  const formElement = () => {
    if (!task) {
      return null;
    }

    let formUiSchema;
    let jsonSchema = task.form_schema;
    let reactFragmentToHideSubmitButton = null;
    if (task.typename === 'ManualTask') {
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
    } else if (task.form_ui_schema) {
      formUiSchema = task.form_ui_schema;
    }
    if (task.state !== 'READY') {
      formUiSchema = Object.assign(formUiSchema || {}, {
        'ui:readonly': true,
      });

      // It doesn't seem as if Form allows for removing the default submit button
      // so passing a blank fragment or children seem to do it though
      //
      // from: https://github.com/rjsf-team/react-jsonschema-form/issues/1602
      reactFragmentToHideSubmitButton = <div />;
    }

    if (task.state === 'READY') {
      let submitButtonText = 'Submit';
      let closeButton = null;
      if (task.typename === 'ManualTask') {
        submitButtonText = 'Continue';
      } else if (task.typename === 'UserTask') {
        closeButton = (
          <Button
            id="close-button"
            onClick={handleCloseButton}
            disabled={formButtonsDisabled}
            kind="secondary"
            title="Save data as draft and close the form."
          >
            Save and Close
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
            {task.signal_buttons.map((signal) => (
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

    const customValidate = (formData: any, errors: any) => {
      return getFieldsWithDateValidations(jsonSchema, formData, errors);
    };

    // we are using two forms here so we can have one that validates data and one that does not.
    // this allows us to autosave form data without extra attributes and without validations
    // but still requires validations when the user submits the form that they can edit.
    return (
      <Grid fullWidth condensed className="megacondensed">
        <Column sm={4} md={5} lg={8}>
          <Form
            id="form-to-submit"
            disabled={formButtonsDisabled}
            formData={taskData}
            onChange={(obj: any) => {
              setTaskData(obj.formData);
              addDebouncedTaskDataAutoSave();
            }}
            onSubmit={handleFormSubmit}
            schema={jsonSchema}
            uiSchema={formUiSchema}
            widgets={rjsfWidgets}
            validator={validator}
            customValidate={customValidate}
            omitExtraData
          >
            {reactFragmentToHideSubmitButton}
          </Form>
          <Form
            id="hidden-form-for-autosave"
            formData={taskData}
            onSubmit={handleAutosaveFormSubmit}
            schema={jsonSchema}
            uiSchema={formUiSchema}
            widgets={rjsfWidgets}
            validator={validator}
            noValidate
            omitExtraData
          />
        </Column>
      </Grid>
    );
  };

  if (task) {
    let statusString = '';
    if (task.state !== 'READY') {
      statusString = ` ${task.state}`;
    }

    return (
      <>
        <ProcessBreadcrumb
          hotCrumbs={[
            [
              `Process Instance Id: ${params.process_instance_id}`,
              `/admin/process-instances/for-me/${modifyProcessIdentifierForPathParam(
                task.process_model_identifier
              )}/${params.process_instance_id}`,
            ],
            [`Task: ${task.name_for_display || task.id}`],
          ]}
        />
        <div>{buildTaskNavigation()}</div>
        <h1>
          Task: {task.name_for_display} ({task.process_model_display_name})
          {statusString}
        </h1>
        <InstructionsForEndUser task={task} />
        {formElement()}
      </>
    );
  }

  return null;
}
