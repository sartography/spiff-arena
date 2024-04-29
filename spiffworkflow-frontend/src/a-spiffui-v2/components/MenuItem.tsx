import { Stack, Typography } from '@mui/material';
import { ReactNode } from 'react';

export default function MenuItem({
  data,
}: {
  data: { label: string; icon: ReactNode; path: string };
}) {
  return (
    <Stack direction="row" gap={3}>
      {data.icon}
      <Typography>{data.label}</Typography>
    </Stack>
  );
}
