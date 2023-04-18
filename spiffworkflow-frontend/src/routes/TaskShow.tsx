import React, { useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import validator from '@rjsf/validator-ajv8';

import {
  TabList,
  Tab,
  Tabs,
  Grid,
  Column,
  ComboBox,
  Button,
  ButtonSet,
} from '@carbon/react';

import MDEditor from '@uiw/react-md-editor';
// eslint-disable-next-line import/no-named-as-default
import Form from '../themes/carbon';
import HttpService from '../services/HttpService';
import useAPIError from '../hooks/UseApiError';
import { modifyProcessIdentifierForPathParam } from '../helpers';
import { ProcessInstanceTask } from '../interfaces';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';

// TODO: move this somewhere else
function TypeAheadWidget({
  id,
  onChange,
  options: { category, itemFormat },
}: {
  id: string;
  onChange: any;
  options: any;
}) {
  const pathForCategory = (inputText: string) => {
    return `/connector-proxy/type-ahead/${category}?prefix=${inputText}&limit=100`;
  };

  const lastSearchTerm = useRef('');
  const [items, setItems] = useState<any[]>([]);
  const [selectedItem, setSelectedItem] = useState<any>(null);
  const itemFormatRegex = /[^{}]+(?=})/g;
  const itemFormatSubstitutions = itemFormat.match(itemFormatRegex);

  const itemToString = (item: any) => {
    if (!item) {
      return null;
    }

    let str = itemFormat;
    itemFormatSubstitutions.forEach((key: string) => {
      str = str.replace(`{${key}}`, item[key]);
    });
    return str;
  };

  const handleTypeAheadResult = (result: any, inputText: string) => {
    if (lastSearchTerm.current === inputText) {
      setItems(result);
    }
  };

  const typeAheadSearch = (inputText: string) => {
    if (inputText) {
      lastSearchTerm.current = inputText;
      // TODO: check cache of prefixes -> results
      HttpService.makeCallToBackend({
        path: pathForCategory(inputText),
        successCallback: (result: any) =>
          handleTypeAheadResult(result, inputText),
      });
    }
  };

  return (
    <ComboBox
      onInputChange={typeAheadSearch}
      onChange={(event: any) => {
        setSelectedItem(event.selectedItem);
        onChange(itemToString(event.selectedItem));
      }}
      id={id}
      items={items}
      itemToString={itemToString}
      placeholder={`Start typing to search for ${category}...`}
      titleText={`Type ahead search for ${category}`}
      selectedItem={selectedItem}
    />
  );
}

class UnexpectedHumanTaskType extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'UnexpectedHumanTaskType';
  }
}

enum FormSubmitType {
  Default,
  Draft,
}

export default function TaskShow() {
  const [task, setTask] = useState<ProcessInstanceTask | null>(null);
  const [userTasks] = useState(null);
  const params = useParams();
  const navigate = useNavigate();
  const [disabled, setDisabled] = useState(false);

  // save current form data so that we can avoid validations in certain situations
  const [currentFormObject, setCurrentFormObject] = useState<any>({});

  const { addError, removeError } = useAPIError();

  // eslint-disable-next-line sonarjs/no-duplicate-string
  const supportedHumanTaskTypes = ['User Task', 'Manual Task'];

  useEffect(() => {
    const processResult = (result: ProcessInstanceTask) => {
      setTask(result);
      setDisabled(false);
      /*  Disable call to load previous tasks -- do not display menu.
      const url = `/v1.0/process-instances/for-me/${modifyProcessIdentifierForPathParam(
        result.process_model_identifier
      )}/${params.process_instance_id}/task-info`;
      // if user is unauthorized to get process-instance task-info then don't do anything
      // Checking like this so we can dynamically create the url with the correct process model
      //  instead of passing the process model identifier in through the params
      HttpService.makeCallToBackend({
        path: url,
        successCallback: (tasks: any) => {
          setDisabled(false);
          setUserTasks(tasks);
        },
        onUnauthorized: () => {
          setDisabled(false);
        },
        failureCallback: (error: any) => {
          addError(error);
        },
      });
      */
    };
    HttpService.makeCallToBackend({
      path: `/tasks/${params.process_instance_id}/${params.task_id}`,
      successCallback: processResult,
      failureCallback: addError,
    });
    // FIXME: not sure what to do about addError. adding it to this array causes the page to endlessly reload
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params]);

  const processSubmitResult = (result: any) => {
    removeError();
    if (result.ok) {
      navigate(`/tasks`);
    } else if (result.process_instance_id) {
      navigate(`/tasks/${result.process_instance_id}/${result.id}`);
    } else {
      addError(result);
    }
  };

  const handleFormSubmit = (
    formObject: any,
    _event: any,
    submitType: FormSubmitType = FormSubmitType.Default
  ) => {
    if (disabled) {
      return;
    }
    let queryParams = '';
    if (submitType === FormSubmitType.Draft) {
      queryParams = '?save_as_draft=true';
    }
    setDisabled(true);
    removeError();
    const dataToSubmit = formObject.formData;
    delete dataToSubmit.isManualTask;
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
          return <Tab selected>{userTask.title}</Tab>;
        }
        if (userTask.state === 'COMPLETED') {
          return (
            <Tab
              onClick={() => navigate(taskUrl)}
              data-qa={`form-nav-${userTask.name}`}
            >
              {userTask.title}
            </Tab>
          );
        }
        if (userTask.state === 'FUTURE') {
          return <Tab disabled>{userTask.title}</Tab>;
        }
        if (userTask.state === 'READY') {
          return (
            <Tab
              onClick={() => navigate(taskUrl)}
              data-qa={`form-nav-${userTask.name}`}
            >
              {userTask.title}
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

  const getFieldsWithDateValidations = (
    jsonSchema: any,
    formData: any,
    errors: any
  ) => {
    if ('properties' in jsonSchema) {
      Object.keys(jsonSchema.properties).forEach((propertyKey: string) => {
        const propertyMetadata = jsonSchema.properties[propertyKey];
        if (
          typeof propertyMetadata === 'object' &&
          'minimumDate' in propertyMetadata &&
          propertyMetadata.minimumDate === 'today'
        ) {
          const dateToday = new Date();
          const dateValue = formData[propertyKey];
          if (dateValue) {
            const dateValueObject = new Date(dateValue);
            const dateValueString = dateValueObject.toISOString().split('T')[0];
            const dateTodayString = dateToday.toISOString().split('T')[0];
            if (dateTodayString > dateValueString) {
              errors[propertyKey].addError('must be today or after');
            }
          }
        }

        // recurse through all nested properties as well
        getFieldsWithDateValidations(
          propertyMetadata,
          formData[propertyKey],
          errors[propertyKey]
        );
      });
    }
    return errors;
  };

  const updateFormData = (formObject: any) => {
    currentFormObject.formData = formObject.formData;
    setCurrentFormObject(currentFormObject);
  };

  const formElement = () => {
    if (!task) {
      return null;
    }

    let formUiSchema;
    let taskData = task.data;
    let jsonSchema = task.form_schema;
    let reactFragmentToHideSubmitButton = null;
    if (task.type === 'Manual Task') {
      taskData = {};
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
      let saveAsDraftButton = null;
      if (task.type === 'Manual Task') {
        submitButtonText = 'Continue';
      } else if (task.type === 'User Task') {
        saveAsDraftButton = (
          <Button
            id="save-as-draft-button"
            disabled={disabled}
            kind="secondary"
            onClick={() =>
              handleFormSubmit(currentFormObject, null, FormSubmitType.Draft)
            }
          >
            Save as draft
          </Button>
        );
      } else {
        throw new UnexpectedHumanTaskType(
          `Invalid task type given: ${task.type}. Only supported types: ${supportedHumanTaskTypes}`
        );
      }
      reactFragmentToHideSubmitButton = (
        <ButtonSet>
          <Button type="submit" id="submit-button" disabled={disabled}>
            {submitButtonText}
          </Button>
          {saveAsDraftButton}
        </ButtonSet>
      );
    }

    const customValidate = (formData: any, errors: any) => {
      return getFieldsWithDateValidations(jsonSchema, formData, errors);
    };

    const widgets = { typeAhead: TypeAheadWidget };

    return (
      <Grid fullWidth condensed>
        <Column sm={4} md={5} lg={8}>
          <Form
            disabled={disabled}
            formData={taskData}
            onSubmit={handleFormSubmit}
            schema={jsonSchema}
            uiSchema={formUiSchema}
            widgets={widgets}
            validator={validator}
            onChange={updateFormData}
            customValidate={customValidate}
            omitExtraData
            liveOmit
          >
            {reactFragmentToHideSubmitButton}
          </Form>
        </Column>
      </Grid>
    );
  };

  const instructionsElement = () => {
    if (!task) {
      return null;
    }
    let instructions = '';
    if (task.properties.instructionsForEndUser) {
      instructions = task.properties.instructionsForEndUser;
    }
    return (
      <div className="markdown">
        {/*
          https://www.npmjs.com/package/@uiw/react-md-editor switches to dark mode by default by respecting @media (prefers-color-scheme: dark)
          This makes it look like our site is broken, so until the rest of the site supports dark mode, turn off dark mode for this component.
        */}
        <div data-color-mode="light">
          <MDEditor.Markdown source={instructions} />
        </div>
      </div>
    );
  };

  if (task) {
    let statusString = '';
    if (task.state !== 'READY') {
      statusString = ` ${task.state}`;
    }

    return (
      <main>
        <ProcessBreadcrumb
          hotCrumbs={[
            [
              `Process Instance Id: ${params.process_instance_id}`,
              `/admin/process-instances/for-me/${modifyProcessIdentifierForPathParam(
                task.process_model_identifier
              )}/${params.process_instance_id}`,
            ],
            [`Task: ${task.title || task.id}`],
          ]}
        />
        <div>{buildTaskNavigation()}</div>
        <h3>
          Task: {task.title} ({task.process_model_display_name}){statusString}
        </h3>
        {instructionsElement()}
        {formElement()}
      </main>
    );
  }

  return null;
}
