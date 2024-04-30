import { Stack, Typography, Button } from '@mui/material';

export default function Toolbar() {
  return (
    <Stack>
      <Stack>
        <Typography variant="h4">Hello</Typography>
        <Typography variant="caption">There</Typography>
      </Stack>
      <Stack>
        <Button title="Hello" variant="contained">
          Start New Process
        </Button>
      </Stack>
    </Stack>
  );
}
