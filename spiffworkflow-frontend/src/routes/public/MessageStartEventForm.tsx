import { Column, Grid, Loading } from '@carbon/react';
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import HttpService from '../../services/HttpService';
import CustomForm from '../../components/CustomForm';
import Page404 from '../Page404';

export default function MessageStartEventForm() {
  const params = useParams();
  const [messageResponse, setMessageResponse] = useState<any>(null);
  const [taskData, setTaskData] = useState<any>(null);

  useEffect(() => {
    HttpService.makeCallToBackend({
      path: `/public/messages/form/${params.modified_message_name}`,
      successCallback: (result: any) => setMessageResponse(result),
      failureCallback: (error: any) => {
        console.error(error);
        setMessageResponse(error);
      },
    });
  }, [params.modified_message_name]);

  if (messageResponse) {
    if (messageResponse.form_schema) {
      return (
        <div className="fixed-width-container">
          <Grid fullWidth condensed className="megacondensed">
            <Column sm={4} md={5} lg={8}>
              <CustomForm
                id="form-to-submit"
                formData={taskData}
                onChange={(obj: any) => {
                  setTaskData(obj.formData);
                }}
                onSubmit={() => console.log('WE SUBMIT')}
                schema={messageResponse.form_schema}
                uiSchema={messageResponse.form_ui_schema}
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
