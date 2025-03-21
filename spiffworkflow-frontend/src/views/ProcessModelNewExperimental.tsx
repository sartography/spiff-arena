import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { TextField, Button, FormControl } from '@mui/material';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import { ProcessModel } from '../interfaces';
import { modifyProcessIdentifierForPathParam } from '../helpers';
import HttpService from '../services/HttpService';

export default function ProcessModelNewExperimental() {
  const params = useParams();
  const navigate = useNavigate();
  const [processModelDescriptiveText, setProcessModelDescriptiveText] =
    useState<string>('');

  const helperText =
    'Create a bug tracker process model with a bug-details form that collects summary, description, and priority';

  const navigateToProcessModel = (result: ProcessModel) => {
    if ('id' in result) {
      const modifiedProcessModelPathFromResult =
        modifyProcessIdentifierForPathParam(result.id);
      navigate(`/process-models/${modifiedProcessModelPathFromResult}`);
    }
  };

  const handleFormSubmission = (event: any) => {
    event.preventDefault();
    HttpService.makeCallToBackend({
      path: `/process-model-natural-language/${params.process_group_id}`,
      successCallback: navigateToProcessModel,
      httpMethod: 'POST',
      postBody: { natural_language_text: processModelDescriptiveText },
    });
  };

  const ohYeeeeaah = () => {
    setProcessModelDescriptiveText(helperText);
  };

  return (
    <>
      <ProcessBreadcrumb
        hotCrumbs={[
          ['Process Groups', '/process-groups'],
          {
            entityToExplode: params.process_group_id || '',
            entityType: 'process-group-id',
            linkLastItem: true,
          },
        ]}
      />
      {/* eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions */}
      <h1 title={helperText} onClick={ohYeeeeaah} onKeyDown={ohYeeeeaah}>
        Add Process Model
      </h1>
      <FormControl component="form" onSubmit={handleFormSubmission}>
        <TextField
          id="process-model-descriptive-text"
          value={processModelDescriptiveText}
          label="Process Model Descriptive Text"
          placeholder="your text"
          onChange={(event: any) =>
            setProcessModelDescriptiveText(event.target.value)
          }
          multiline
          rows={4}
          variant="outlined"
        />
        <Button variant="contained" color="primary" type="submit">
          Submit
        </Button>
      </FormControl>
    </>
  );
}
