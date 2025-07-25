import { Box, CircularProgress, Grid } from '@mui/material';
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import HttpService from '../../services/HttpService';
import CustomForm from '../../components/CustomForm';
import { recursivelyChangeNullAndUndefined } from '../../helpers';
import { ErrorForDisplay, PublicTask } from '../../interfaces';
import MarkdownRenderer from '../../components/MarkdownRenderer';
import InstructionsForEndUser from '../../components/InstructionsForEndUser';
import {
  ErrorDisplayStateless,
  errorForDisplayFromString,
} from '../../components/ErrorDisplay';
import Page404 from '../Page404';

export default function PublicForm() {
  const params = useParams();
  const [taskData, setTaskData] = useState<any>(null);
  const [formButtonsDisabled, setFormButtonsDisabled] = useState(false);
  const [confirmationMessage, setConfirmationMessage] = useState<string | null>(
    null,
  );
  const [publicTask, setPublicTask] = useState<PublicTask | null>(null);
  const [currentPageError, setCurrentPageError] =
    useState<ErrorForDisplay | null>(null);
  const { t } = useTranslation();

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
        if (
          error.error_code === 'message_triggerable_process_model_not_found'
        ) {
          setCurrentPageError(error);
        } else {
          setCurrentPageError(
            errorForDisplayFromString(t('error_retrieving_content')),
          );
        }
        console.error(error);
      },
    });
  }, [
    params.modified_message_name,
    params.process_instance_id,
    params.task_guid,
    t,
  ]);

  const processSubmitResult = (result: PublicTask) => {
    setCurrentPageError(null);
    setFormButtonsDisabled(false);
    setPublicTask(result);
    if (result.confirmation_message_markdown) {
      setConfirmationMessage(result.confirmation_message_markdown);
    } else if (!result.form) {
      setConfirmationMessage(`${t('thank_you')}!`);
    }
  };

  const handleFormSubmit = (formObject: any, _event: any) => {
    if (formButtonsDisabled) {
      return;
    }

    const dataToSubmit = formObject?.formData;
    delete dataToSubmit.isManualTask;

    setFormButtonsDisabled(true);
    setCurrentPageError(null);

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
        setCurrentPageError(error);
      },
      httpMethod,
      postBody: dataToSubmit,
    });
  };

  const innerComponents = () => {
    if (currentPageError) {
      if (
        currentPageError.error_code ===
        'message_triggerable_process_model_not_found'
      ) {
        return <Page404 />;
      }
      return (
        <>
          <ErrorDisplayStateless errorObject={currentPageError} />
          <p>
            Go to{' '}
            <a href="/" data-testid="public-home-link">
              {t('home')}
            </a>
          </p>
        </>
      );
    }

    if (confirmationMessage) {
      return <MarkdownRenderer source={confirmationMessage} />;
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
        <>
          <InstructionsForEndUser
            defaultMessage={publicTask.form.instructions_for_end_user}
          />
          <Grid container spacing={2}>
            <Grid item xs={12} sm={8}>
              <CustomForm
                id={`form-to-submit-${publicTask.task_guid}`}
                key={`form-to-submit-${publicTask.task_guid}`}
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
            </Grid>
          </Grid>
        </>
      );
    }
    const style = { margin: '50px 0 50px 50px' };
    return (
      <Box sx={style}>
        <CircularProgress />
      </Box>
    );
  };

  return <div className="fixed-width-container">{innerComponents()}</div>;
}
