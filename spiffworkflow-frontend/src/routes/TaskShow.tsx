import { useContext, useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

// FIXME: npm install @rjsf/validator-ajv8 and use it as soon as
// rawErrors is fixed.
// https://react-jsonschema-form.readthedocs.io/en/latest/usage/validation/
// https://github.com/rjsf-team/react-jsonschema-form/issues/2309 links to a codesandbox that might be useful to fork
// if we wanted to file a defect against rjsf to show the difference between validator-ajv6 and validator-ajv8.
// https://github.com/rjsf-team/react-jsonschema-form/blob/main/docs/api-reference/uiSchema.md talks about rawErrors
import validator from '@rjsf/validator-ajv6';

// @ts-ignore
import { Button, Stack } from '@carbon/react';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
// eslint-disable-next-line import/no-named-as-default
import Form from '../themes/carbon';
import HttpService from '../services/HttpService';
import ErrorContext from '../contexts/ErrorContext';
import { modifyProcessModelPath } from '../helpers';

export default function TaskShow() {
  const [task, setTask] = useState(null);
  const [userTasks, setUserTasks] = useState(null);
  const params = useParams();
  const navigate = useNavigate();

  const setErrorMessage = (useContext as any)(ErrorContext)[1];

  useEffect(() => {
    const processResult = (result: any) => {
      setTask(result);
      HttpService.makeCallToBackend({
        path: `/process-instances/${modifyProcessModelPath(
          result.process_model_identifier
        )}/${params.process_instance_id}/tasks`,
        successCallback: setUserTasks,
      });
    };

    HttpService.makeCallToBackend({
      path: `/tasks/${params.process_instance_id}/${params.task_id}`,
      successCallback: processResult,
      // This causes the page to continuously reload
      // failureCallback: setErrorMessage,
    });
  }, [params]);

  const processSubmitResult = (result: any) => {
    setErrorMessage(null);
    if (result.ok) {
      navigate(`/tasks`);
    } else if (result.process_instance_id) {
      navigate(`/tasks/${result.process_instance_id}/${result.id}`);
    } else {
      setErrorMessage(`Received unexpected error: ${result.message}`);
    }
  };

  const handleFormSubmit = (event: any) => {
    setErrorMessage(null);
    const dataToSubmit = event.formData;
    delete dataToSubmit.isManualTask;
    HttpService.makeCallToBackend({
      path: `/tasks/${params.process_instance_id}/${params.task_id}`,
      successCallback: processSubmitResult,
      failureCallback: setErrorMessage,
      httpMethod: 'PUT',
      postBody: dataToSubmit,
    });
  };

  const buildTaskNavigation = () => {
    let userTasksElement;
    if (userTasks) {
      userTasksElement = (userTasks as any).map(function getUserTasksElement(
        userTask: any
      ) {
        const taskUrl = `/tasks/${params.process_instance_id}/${userTask.id}`;
        if (userTask.id === params.task_id) {
          return <span>{userTask.name}</span>;
        }
        if (userTask.state === 'COMPLETED') {
          return (
            <Link to={taskUrl} data-qa={`form-nav-${userTask.name}`}>
              {userTask.name}
            </Link>
          );
        }
        if (userTask.state === 'FUTURE') {
          return <span style={{ color: 'red' }}>{userTask.name}</span>;
        }
        if (userTask.state === 'READY') {
          return (
            <Link to={taskUrl} data-qa={`form-nav-${userTask.name}`}>
              {userTask.name} - Current
            </Link>
          );
        }
        return null;
      });
    }
    return (
      <Stack orientation="horizontal" gap={3}>
        <Button href="/tasks">Go Back To List</Button>
        {userTasksElement}
      </Stack>
    );
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

    return (
      <Form
        formData={taskData}
        onSubmit={handleFormSubmit}
        schema={jsonSchema}
        uiSchema={formUiSchema}
        validator={validator}
      >
        {reactFragmentToHideSubmitButton}
      </Form>
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
