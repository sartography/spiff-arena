import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, TextField, Box } from '@mui/material';
import { isANumber, modifyProcessIdentifierForPathParam } from '../helpers';
import HttpService from '../services/HttpService';
import ProcessInstanceListTabs from '../components/ProcessInstanceListTabs';
import { ProcessInstance } from '../interfaces';

export default function ProcessInstanceFindById() {
  const navigate = useNavigate();
  const [processInstanceId, setProcessInstanceId] = useState<string>('');
  const [processInstanceIdValid, setProcessInstanceIdValid] =
    useState<boolean>(true);

  useEffect(() => {}, []);

  const handleProcessInstanceNavigation = (result: any) => {
    const processInstance: ProcessInstance = result.process_instance;
    let path = '/process-instances/';
    if (result.uri_type === 'for-me') {
      path += 'for-me/';
    }
    path += `${modifyProcessIdentifierForPathParam(
      processInstance.process_model_identifier,
    )}/${processInstance.id}`;
    navigate(path);
  };

  const handleFormSubmission = (event: any) => {
    event.preventDefault();

    if (!processInstanceId) {
      setProcessInstanceIdValid(false);
    }

    if (processInstanceId && processInstanceIdValid) {
      HttpService.makeCallToBackend({
        path: `/process-instances/find-by-id/${processInstanceId}`,
        successCallback: handleProcessInstanceNavigation,
      });
    }
  };

  const handleProcessInstanceIdChange = (event: any) => {
    if (isANumber(event.target.value)) {
      setProcessInstanceIdValid(true);
    } else {
      setProcessInstanceIdValid(false);
    }
    setProcessInstanceId(event.target.value);
  };

  const formElements = () => {
    return (
      <TextField
        id="process-instance-id-input"
        error={!processInstanceIdValid}
        helperText={
          !processInstanceIdValid ? 'Process Instance Id must be a number.' : ''
        }
        label="Process Instance Id*"
        value={processInstanceId}
        onChange={handleProcessInstanceIdChange}
        fullWidth
      />
    );
  };

  const formButtons = () => {
    return (
      <Button type="submit" variant="contained">
        Submit
      </Button>
    );
  };

  return (
    <>
      <ProcessInstanceListTabs variant="find-by-id" />
      <br />
      <Box component="form" onSubmit={handleFormSubmission} sx={{ mt: 1 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {formElements()}
          {formButtons()}
        </Box>
      </Box>
    </>
  );
}
