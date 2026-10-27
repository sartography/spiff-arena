import { Box, useTheme } from '@mui/material';
import SpiffLogoMark from '../assets/icons/spiffworks_arena.svg';

/**
 * The SpiffWorks Arena logo, wordmark included in the SVG itself.
 *
 * The artwork is baked as near-black shapes on a transparent background, so
 * it disappears against the dark-mode background. There's no separate
 * light-on-dark asset, so we invert it in dark mode -- since the source is
 * effectively pure black-on-transparent, this cleanly produces near-white
 * on transparent rather than a color shift.
 *
 * The mark is decorative: callers wrap it in a link that carries the
 * accessible name, so it's hidden from assistive tech here.
 */
export default function SpiffLogo() {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';
  return (
    <Box
      aria-hidden="true"
      sx={{
        display: 'inline-flex',
        alignItems: 'center',
        maxWidth: '100%',
        '& svg': {
          height: 42,
          width: 'auto',
          maxWidth: '100%',
          filter: isDark ? 'invert(1)' : 'none',
        },
      }}
    >
      <SpiffLogoMark />
    </Box>
  );
}
