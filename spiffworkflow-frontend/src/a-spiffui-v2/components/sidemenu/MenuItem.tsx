import { Stack, Typography, useTheme } from '@mui/material';
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
  const isDark = useTheme().palette.mode === 'dark';
  return (
    <Stack
      direction="row"
      borderRadius={5}
      gap={2}
      padding={1}
      onClick={() => callback(data)}
      alignItems="center"
      sx={{
        ':hover': { backgroundColor: isDark ? 'primary.main' : purple[50] },
        cursor: 'default',
      }}
    >
      <Typography sx={{ color: 'text.primary', paddingTop: 1 }}>
        {data.icon}
      </Typography>
      <Typography color="text.primary">{data.label}</Typography>
    </Stack>
  );
}
