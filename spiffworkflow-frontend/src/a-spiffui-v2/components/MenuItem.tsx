import { Stack, Typography } from '@mui/material';
import { purple } from '@mui/material/colors';
import { ReactNode } from 'react';

export default function MenuItem({
  data,
}: {
  data: { label: string; icon: ReactNode; path: string };
}) {
  return (
    <Stack
      direction="row"
      borderRadius={5}
      gap={2}
      padding={1}
      sx={{ ':hover': { backgroundColor: purple[50] }, cursor: 'default' }}
    >
      {data.icon}
      <Typography>{data.label}</Typography>
    </Stack>
  );
}
