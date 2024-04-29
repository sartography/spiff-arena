import { Stack, Typography } from '@mui/material';
import { ReactNode } from 'react';

export default function MenuItem({
  data,
  iconsize,
}: {
  data: { label: string; icon: ReactNode; path: string };
  iconsize?: string;
}) {
  return (
    <Stack direction="row">
      {data.icon}
      <Typography>{data.label}</Typography>
    </Stack>
  );
}
