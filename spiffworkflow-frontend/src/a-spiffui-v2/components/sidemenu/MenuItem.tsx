import { Stack, Typography } from '@mui/material';
import { purple } from '@mui/material/colors';
import { ReactNode } from 'react';

/**
 * MenuItem component that satisfies design requirements.
 * Very basic click 'n handle sort of thing.
 */
export type MenuItemData = { label: string; icon: ReactNode; path: string };
export default function MenuItem({
  data,
  callback,
}: {
  data: MenuItemData;
  callback: (arg: MenuItemData) => void;
}) {
  return (
    <Stack
      direction="row"
      borderRadius={5}
      gap={2}
      padding={1}
      onClick={() => callback(data)}
      sx={{ ':hover': { backgroundColor: purple[50] }, cursor: 'default' }}
    >
      {data.icon}
      <Typography>{data.label}</Typography>
    </Stack>
  );
}
