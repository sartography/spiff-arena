import { useTheme } from '@mui/material';

export default function useSpiffTheme() {
  const { palette } = useTheme();
  const isDark = palette.mode === 'dark';
  return { isDark };
}
