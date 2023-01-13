import { useContext, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import validator from '@rjsf/validator-ajv8';

import {
  TabList,
  Tab,
  Tabs,
  Grid,
  Column,
  Button,
  // @ts-ignore
} from '@carbon/react';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
// eslint-disable-next-line import/no-named-as-default
import Form from '../themes/carbon';
import HttpService from '../services/HttpService';
import ErrorContext from '../contexts/ErrorContext';
import { modifyProcessIdentifierForPathParam } from '../helpers';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import { PermissionsToCheck } from '../interfaces';
import { usePermissionFetcher } from '../hooks/PermissionService';

export default function TaskShow() {
  const [task, setTask] = useState(null);
  const [userTasks, setUserTasks] = useState(null);
  const params = useParams();
  const navigate = useNavigate();

  const setErrorObject = (useContext as any)(ErrorContext)[1];

  const { targetUris } = useUriListForPermissions();
  const permissionRequestData: PermissionsToCheck = {
    [targetUris.processInstanceTaskListDataPath]: ['GET'],
  };
  const { ability, permissionsLoaded } = usePermissionFetcher(
    permissionRequestData
  );

  useEffect(() => {
    if (permissionsLoaded) {
      const processResult = (result: any) => {
        setTask(result);
        if (ability.can('GET', targetUris.processInstanceTaskListDataPath)) {
          HttpService.makeCallToBackend({
            path: `/task-data/${modifyProcessIdentifierForPathParam(
              result.process_model_identifier
            )}/${params.process_instance_id}`,
            successCallback: setUserTasks,
          });
        }
      };

      HttpService.makeCallToBackend({
        path: `/tasks/${params.process_instance_id}/${params.task_id}`,
        successCallback: processResult,
        // This causes the page to continuously reload
        // failureCallback: setErrorObject,
      });
    }
  }, [params, permissionsLoaded, ability, targetUris]);

  const processSubmitResult = (result: any) => {
    setErrorObject(null);
    if (result.ok) {
      navigate(`/tasks`);
    } else if (result.process_instance_id) {
      navigate(`/tasks/${result.process_instance_id}/${result.id}`);
    } else {
      setErrorObject(`Received unexpected error: ${result.message}`);
    }
  };

  const handleFormSubmit = (event: any) => {
    setErrorObject(null);
    const dataToSubmit = event.formData;
    delete dataToSubmit.isManualTask;
    HttpService.makeCallToBackend({
      path: `/tasks/${params.process_instance_id}/${params.task_id}`,
      successCallback: processSubmitResult,
      failureCallback: setErrorObject,
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

  const formElement = (taskToUse: any) => {
    let formUiSchema;
    let taskData = taskToUse.data;
    let jsonSchema = taskToUse.form_schema;
    let reactFragmentToHideSubmitButton = null;
    if (taskToUse.type === 'Manual Task') {
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
    } else if (taskToUse.form_ui_schema) {
      formUiSchema = JSON.parse(taskToUse.form_ui_schema);
    }
    if (taskToUse.state !== 'READY') {
      formUiSchema = Object.assign(formUiSchema || {}, {
        'ui:readonly': true,
      });

      // It doesn't seem as if Form allows for removing the default submit button
      // so passing a blank fragment or children seem to do it though
      //
      // from: https://github.com/rjsf-team/react-jsonschema-form/issues/1602
      reactFragmentToHideSubmitButton = <div />;
    }

    if (taskToUse.type === 'Manual Task' && taskToUse.state === 'READY') {
      reactFragmentToHideSubmitButton = (
        <div>
          <Button type="submit">Continue</Button>
        </div>
      );
    }

    function customValidate(formData: any, errors: any) {
      if (formData.pass1 !== formData.pass2) {
        errors.pass2.addError("Passwords don't match");
      }
      return errors;
    }

    return (
      <Grid fullWidth condensed>
        <Column md={5} lg={8} sm={4}>
          <Form
            formData={taskData}
            onSubmit={handleFormSubmit}
            schema={jsonSchema}
            uiSchema={formUiSchema}
            validator={validator}
            customValidate={customValidate}
          >
            {reactFragmentToHideSubmitButton}
          </Form>
        </Column>
      </Grid>
    );
  };

  const instructionsElement = (taskToUse: any) => {
    let instructions = '';
    if (taskToUse.properties.instructionsForEndUser) {
      instructions = taskToUse.properties.instructionsForEndUser;
    }
    return (
      <div className="markdown">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {instructions}
        </ReactMarkdown>
      </div>
    );
  };

  if (task) {
    const taskToUse = task as any;
    let statusString = '';
    if (taskToUse.state !== 'READY') {
      statusString = ` ${taskToUse.state}`;
    }

    return (
      <main>
        <div>{buildTaskNavigation()}</div>
        <h3>
          Task: {taskToUse.title} ({taskToUse.process_model_display_name})
          {statusString}
        </h3>
        {instructionsElement(taskToUse)}
        {formElement(taskToUse)}
      </main>
    );
  }

  return null;
}
