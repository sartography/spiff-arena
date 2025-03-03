import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { TextField, Button, Stack, Box, Typography } from '@mui/material';
import HttpService from '../services/HttpService';

export default function SecretNew() {
  const [value, setValue] = useState<string>('');
  const [key, setKey] = useState<string>('');
  const [keyIsInvalid, setKeyIsInvalid] = useState<boolean>(false);
  const [valueIsInvalid, setValueIsInvalid] = useState<boolean>(false);
  const navigate = useNavigate();

  const navigateToSecret = (_result: any) => {
    navigate(`/configuration/secrets/${key}`);
  };

  const navigateToSecrets = () => {
    navigate(`/configuration/secrets`);
  };

  const addSecret = (event: any) => {
    event.preventDefault();

    let hasErrors = false;
    setKeyIsInvalid(false);
    if (!key.match(/^[\w-]+$/)) {
      setKeyIsInvalid(true);
      hasErrors = true;
    }
    setValueIsInvalid(false);
    if (value.trim().length < 1) {
      setValueIsInvalid(true);
      hasErrors = true;
    }
    if (hasErrors) {
      return;
    }

    HttpService.makeCallToBackend({
      path: `/secrets`,
      successCallback: navigateToSecret,
      httpMethod: 'POST',
      postBody: {
        key,
        value,
      },
    });
  };

  return (
    <Box component="main" sx={{ padding: '1rem 0' }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Add Secret
      </Typography>
      <form onSubmit={addSecret}>
        <Stack spacing={2}>
          <TextField
            id="secret-key"
            label="Key*"
            value={key}
            error={keyIsInvalid}
            helperText={
              keyIsInvalid
                ? 'The key must be alphanumeric characters and underscores'
                : ''
            }
            onChange={(e: any) => setKey(e.target.value)}
            fullWidth
          />
          <TextField
            id="secret-value"
            label="Value*"
            value={value}
            error={valueIsInvalid}
            helperText={valueIsInvalid ? 'The value must be set' : ''}
            onChange={(e: any) => {
              setValue(e.target.value);
            }}
            fullWidth
          />
          <Stack direction="row" spacing={2}>
            <Button variant="outlined" onClick={navigateToSecrets}>
              Cancel
            </Button>
            <Button variant="contained" type="submit">
              Submit
            </Button>
          </Stack>
        </Stack>
      </form>
    </Box>
  );
}
