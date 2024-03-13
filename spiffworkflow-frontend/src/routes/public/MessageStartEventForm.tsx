import { Column, Grid, Loading } from '@carbon/react';
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import HttpService from '../../services/HttpService';
import CustomForm from '../../components/CustomForm';
import Page404 from '../Page404';
import { recursivelyChangeNullAndUndefined } from '../../helpers';
import useAPIError from '../../hooks/UseApiError';
import { PublicTaskForm, PublicTaskSubmitResponse } from '../../interfaces';

export default function MessageStartEventForm() {
  const params = useParams();
  const [formContents, setFormContents] = useState<PublicTaskForm | null>(null);
  const [taskData, setTaskData] = useState<any>(null);
  const [formButtonsDisabled, setFormButtonsDisabled] = useState(false);
  const { addError, removeError } = useAPIError();
  const [formSubmitResult, setFormSubmitResult] = useState<string | null>(null);
  const [taskSubmitResponse, setTaskSubmitResponse] =
    useState<PublicTaskSubmitResponse | null>(null);

  useEffect(() => {
    HttpService.makeCallToBackend({
      path: `/public/messages/form/${params.modified_message_name}`,
      successCallback: (result: PublicTaskForm) => setFormContents(result),
      failureCallback: (error: any) => {
        console.error(error);
      },
    });
  }, [params.modified_message_name]);

  const processSubmitResult = (result: PublicTaskSubmitResponse) => {
    removeError();
    setFormButtonsDisabled(false);
    setTaskSubmitResponse(result);
    if (result.form) {
      setFormContents(result.form);
    } else if (result.instructions) {
      setFormSubmitResult(result.instructions);
    } else {
      setFormSubmitResult('We DONE');
    }
  };

  const handleFormSubmit = (formObject: any, _event: any) => {
    if (formButtonsDisabled) {
      return;
    }

    const dataToSubmit = formObject?.formData;

    setFormButtonsDisabled(true);
    removeError();

    recursivelyChangeNullAndUndefined(dataToSubmit, null);
    let path = `/public/messages/submit/${params.modified_message_name}`;
    let httpMethod = 'POST';
    if (
      taskSubmitResponse?.task_guid &&
      taskSubmitResponse?.process_instance_id
    ) {
      path = `/public/tasks/${taskSubmitResponse.process_instance_id}/${taskSubmitResponse.task_guid}`;
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

  if (formSubmitResult) {
    return <h1>{formSubmitResult}</h1>;
  }
  if (formContents) {
    if (formContents.form_schema) {
      return (
        <div className="fixed-width-container">
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
                schema={formContents.form_schema}
                uiSchema={formContents.form_ui_schema}
                restrictedWidth
                reactJsonSchemaForm="mui"
              />
            </Column>
          </Grid>
        </div>
      );
    }
    return <Page404 />;
  }
  const style = { margin: '50px 0 50px 50px' };
  return (
    <Loading
      description="Active loading indicator"
      withOverlay={false}
      style={style}
    />
  );
}
