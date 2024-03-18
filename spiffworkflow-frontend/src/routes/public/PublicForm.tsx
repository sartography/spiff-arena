import { Column, Grid, Loading } from '@carbon/react';
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import HttpService from '../../services/HttpService';
import CustomForm from '../../components/CustomForm';
import { recursivelyChangeNullAndUndefined } from '../../helpers';
import useAPIError from '../../hooks/UseApiError';
import { PublicTask } from '../../interfaces';
import MarkdownRenderer from '../../components/MarkdownRenderer';
import InstructionsForEndUser from '../../components/InstructionsForEndUser';

export default function PublicForm() {
  const params = useParams();
  const [taskData, setTaskData] = useState<any>(null);
  const [formButtonsDisabled, setFormButtonsDisabled] = useState(false);
  const { addError, removeError } = useAPIError();
  const [confirmationMessage, setConfirmationMessage] = useState<string | null>(
    null
  );
  const [publicTask, setPublicTask] = useState<PublicTask | null>(null);

  useEffect(() => {
    const taskGuid = params.task_guid;
    const processInstanceId = params.process_instance_id;
    let url = `/public/messages/form/${params.modified_message_name}`;
    if (taskGuid) {
      url = `/public/tasks/${processInstanceId}/${taskGuid}`;
    }
    HttpService.makeCallToBackend({
      path: url,
      successCallback: (result: PublicTask) => setPublicTask(result),
      failureCallback: (error: any) => {
        console.error(error);
      },
    });
  }, [
    params.modified_message_name,
    params.process_instance_id,
    params.task_guid,
  ]);

  const processSubmitResult = (result: PublicTask) => {
    removeError();
    setFormButtonsDisabled(false);
    setPublicTask(result);
    if (result.confirmation_message_markdown) {
      setConfirmationMessage(result.confirmation_message_markdown);
    } else if (!result.form) {
      setConfirmationMessage('Thank you!');
    }
  };

  const handleFormSubmit = (formObject: any, _event: any) => {
    if (formButtonsDisabled) {
      return;
    }

    const dataToSubmit = formObject?.formData;
    delete dataToSubmit.isManualTask;

    setFormButtonsDisabled(true);
    removeError();

    // removing this will force the loading icon to appear.
    // we could also set a state for it at some point but this seemed
    // like a way to reduce states.
    setPublicTask(null);

    recursivelyChangeNullAndUndefined(dataToSubmit, null);
    let path = `/public/messages/submit/${params.modified_message_name}`;
    let httpMethod = 'POST';
    if (publicTask?.task_guid && publicTask?.process_instance_id) {
      path = `/public/tasks/${publicTask.process_instance_id}/${publicTask.task_guid}`;
      httpMethod = 'PUT';
    }

    HttpService.makeCallToBackend({
      path: `${path}?execution_mode=synchronous`,
      successCallback: processSubmitResult,
      failureCallback: (error: any) => {
        addError(error);
      },
      httpMethod,
      postBody: dataToSubmit,
    });
  };

  if (confirmationMessage) {
    return (
      <div className="fixed-width-container">
        <MarkdownRenderer linkTarget="_blank" source={confirmationMessage} />
      </div>
    );
  }
  if (publicTask) {
    let jsonSchema = publicTask.form.form_schema;
    let formUiSchema = publicTask.form.form_ui_schema;
    if (!jsonSchema) {
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
    }
    return (
      <div className="fixed-width-container">
        <InstructionsForEndUser
          defaultMessage={publicTask.form.instructions_for_end_user}
        />
        <Grid fullWidth condensed className="megacondensed">
          <Column sm={4} md={5} lg={8}>
            <CustomForm
              id="form-to-submit"
              disabled={formButtonsDisabled}
              formData={taskData}
              onChange={(obj: any) => {
                setTaskData(obj.formData);
              }}
              onSubmit={handleFormSubmit}
              schema={jsonSchema}
              uiSchema={formUiSchema}
              restrictedWidth
              reactJsonSchemaForm="mui"
            />
          </Column>
        </Grid>
      </div>
    );
  }
  const style = { margin: '50px 0 50px 50px' };
  return (
    <div className="fixed-width-container">
      <Loading
        description="Active loading indicator"
        withOverlay={false}
        style={style}
      />
    </div>
  );
}
