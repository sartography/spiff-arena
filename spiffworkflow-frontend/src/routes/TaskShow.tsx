import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import validator from '@rjsf/validator-ajv8';

import { Grid, Column, Button, ButtonSet, Loading } from '@carbon/react';

import { useDebouncedCallback } from 'use-debounce';
import { Form } from '../rjsf/carbon_theme';
import HttpService from '../services/HttpService';
import useAPIError from '../hooks/UseApiError';
import {
  doNothing,
  modifyProcessIdentifierForPathParam,
  recursivelyChangeNullAndUndefined,
} from '../helpers';
import { BasicTask, EventDefinition, Task } from '../interfaces';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import InstructionsForEndUser from '../components/InstructionsForEndUser';
import TypeaheadWidget from '../rjsf/custom_widgets/TypeaheadWidget/TypeaheadWidget';
import DateRangePickerWidget from '../rjsf/custom_widgets/DateRangePicker/DateRangePickerWidget';
import { DATE_RANGE_DELIMITER } from '../config';

export default function TaskShow() {
  const [basicTask, setBasicTask] = useState<BasicTask | null>(null);
  const [taskWithTaskData, setTaskWithTaskData] = useState<Task | null>(null);
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
  const navigateToInterstitial = (myTask: BasicTask) => {
    navigate(
      `/admin/process-instances/for-me/${modifyProcessIdentifierForPathParam(
        myTask.process_model_identifier
      )}/${myTask.process_instance_id}/interstitial`
    );
  };

  useEffect(() => {
    const processBasicTaskResult = (result: BasicTask) => {
      setBasicTask(result);
      if (!result.can_complete) {
        navigateToInterstitial(result);
      }
    };
    const processTaskWithDataResult = (result: Task) => {
      setTaskWithTaskData(result);

      // convert null back to undefined so rjsf doesn't attempt to incorrectly validate them
      const taskDataToUse = result.saved_form_data || result.data;
      setTaskData(recursivelyChangeNullAndUndefined(taskDataToUse, undefined));
      setFormButtonsDisabled(false);
    };

    HttpService.makeCallToBackend({
      path: `/tasks/${params.process_instance_id}/${params.task_id}`,
      successCallback: processBasicTaskResult,
      failureCallback: addError,
    });
    HttpService.makeCallToBackend({
      path: `/tasks/${params.process_instance_id}/${params.task_id}?with_form_data=true`,
      successCallback: processTaskWithDataResult,
      failureCallback: addError,
    });
    // FIXME: not sure what to do about addError. adding it to this array causes the page to endlessly reload
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params]);

  // Before we auto-saved form data, we remembered what data was in the form, and then created a synthetic submit event
  // in order to implement a "Save and close" button. That button no longer saves (since we have auto-save), but the crazy
  // frontend code to support that Save and close button is here, in case we need to reference that someday:
  //   https://github.com/sartography/spiff-arena/blob/182f56a1ad23ce780e8f5b0ed00efac3e6ad117b/spiffworkflow-frontend/src/routes/TaskShow.tsx#L329
  const autoSaveTaskData = (formData: any, successCallback?: Function) => {
    // save-draft gets called when a manual task form loads but there's no data to save so don't do it
    if (taskWithTaskData?.typename === 'ManualTask') {
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
    // field format:
    //    field:[field_name_to_use]
    //
    // if field is a range:
    //    field:[field_name_to_use]:[start or end]
    //
    // defaults to "start" in all cases
    const [_, fieldIdentifierToCompareWith, startOrEnd] =
      minimumDateCheck.split(':');
    if (!(fieldIdentifierToCompareWith in formData)) {
      errors[propertyKey].addError(
        `was supposed to be compared against '${fieldIdentifierToCompareWith}' but it either doesn't have a value or does not exist`
      );
      return;
    }

    const rawDateToCompareWith = formData[fieldIdentifierToCompareWith];
    if (!rawDateToCompareWith) {
      errors[propertyKey].addError(
        `was supposed to be compared against '${fieldIdentifierToCompareWith}' but that field did not have a value`
      );
      return;
    }

    const [startDate, endDate] =
      rawDateToCompareWith.split(DATE_RANGE_DELIMITER);
    let dateToCompareWith = startDate;
    if (startOrEnd && startOrEnd === 'end') {
      dateToCompareWith = endDate;
    }

    if (!dateToCompareWith) {
      const errorMessage = `was supposed to be compared against '${[
        fieldIdentifierToCompareWith,
        startOrEnd,
      ].join(':')}' but that field did not have a value`;
      errors[propertyKey].addError(errorMessage);
      return;
    }

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
  };

  const checkMinimumDate = (
    formData: any,
    propertyKey: string,
    propertyMetadata: any,
    errors: any,
    jsonSchema: any
  ) => {
    // can be either "today" or another field
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
    if (!taskWithTaskData) {
      return null;
    }

    let formUiSchema;
    let jsonSchema = taskWithTaskData.form_schema;
    let reactFragmentToHideSubmitButton = null;
    if (taskWithTaskData.typename === 'ManualTask') {
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
      let submitButtonText = 'Submit';
      let closeButton = null;
      if (taskWithTaskData.typename === 'ManualTask') {
        submitButtonText = 'Continue';
      } else if (taskWithTaskData.typename === 'UserTask') {
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

    const customValidate = (formData: any, errors: any) => {
      return getFieldsWithDateValidations(jsonSchema, formData, errors);
    };

    // we are using two forms here so we can have one that validates data and one that does not.
    // this allows us to autosave form data without extra attributes and without validations
    // but still requires validations when the user submits the form that they can edit.
    return (
      <Grid fullWidth condensed>
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

  const pageElements = [];
  if (basicTask) {
    let statusString = '';
    if (basicTask.state !== 'READY') {
      statusString = ` ${basicTask.state}`;
    }

    pageElements.push(
      <ProcessBreadcrumb
        hotCrumbs={[
          [
            `Process Instance Id: ${params.process_instance_id}`,
            `/admin/process-instances/for-me/${modifyProcessIdentifierForPathParam(
              basicTask.process_model_identifier
            )}/${params.process_instance_id}`,
          ],
          [`Task: ${basicTask.name_for_display || basicTask.id}`],
        ]}
      />
    );
    pageElements.push(
      <h3>
        Task: {basicTask.name_for_display} (
        {basicTask.process_model_display_name}){statusString}
      </h3>
    );
  }
  if (basicTask && taskData) {
    pageElements.push(<InstructionsForEndUser task={taskWithTaskData} />);
    pageElements.push(formElement());
  } else {
    pageElements.push(getLoadingIcon());
  }

  // typescript gets angry if we return an array of elements not in a tag
  // eslint-disable-next-line react/jsx-no-useless-fragment
  return <>{pageElements}</>;
}
