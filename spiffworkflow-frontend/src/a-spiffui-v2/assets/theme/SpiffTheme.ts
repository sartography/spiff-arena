import { ThemeOptions } from '@mui/material';
import { deepPurple } from '@mui/material/colors';

/**
 * This is fed to the MUI ThemeProvider at the top of the app.
 * The primary and secondary colors are "Web3" purple/grey shades.
 */
export const globalTheme: ThemeOptions = {
  // Alter theme to be more "Web3" purple/grey shades
  palette: {
    primary: { main: deepPurple[500] },
    // Taken from Material 3 Figma file secondary color.
    // Not sure what it equates to in the standard palette.
    secondary: { main: '#625B71' },
  },
  typography: {
    // Poppins is pulled in from the Google Fonts CDN in index.html
    // TODO: Install fonts locally?
    fontFamily: `"Poppins", "Roboto", "Arial", "Helvetica", sans-serif`,
    fontSize: 14,
    fontWeightLight: 300,
    fontWeightRegular: 400,
    fontWeightMedium: 500,
    button: {
      textTransform: 'none',
    },
  },
  components: {
    // We wanted rounded buttons everywhere
    MuiButton: {
      styleOverrides: {
        root: {
          fontSize: '1rem',
          borderRadius: 100,
        },
      },
    },
  },
};
