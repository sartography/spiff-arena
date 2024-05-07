import { PaletteMode, ThemeOptions } from '@mui/material';
import { blue, green, indigo, orange, purple, red } from '@mui/material/colors';

const customNotifications = (mode: PaletteMode) => {
  return mode === 'light'
    ? {
        success: {
          main: green[100],
          light: green[100],
          dark: green[500],
        },
        warning: {
          main: orange[100],
          light: orange[100],
          dark: orange[500],
        },
        error: {
          main: red[100],
          light: red[100],
          dark: red[500],
        },
        info: {
          main: blue[100],
          light: blue[100],
          dark: blue[500],
        },
      }
    : {
        success: {
          main: green[500],
          light: green[300],
          dark: green[700],
          contrastText: '#fff',
        },
        warning: {
          main: orange[300],
          light: orange[500],
          dark: orange[700],
          contrastText: '#fff',
        },
        error: {
          main: red[300],
          light: red[500],
          dark: red[700],
          contrastText: '#fff',
        },
        info: {
          main: blue[300],
          light: blue[500],
          dark: blue[700],
          contrastText: '#fff',
        },
      };
};

const customComponents = (mode: PaletteMode) => {
  // We wanted rounded buttons everywhere
  return {
    MuiButton: {
      styleOverrides: {
        root: {
          fontSize: '1rem',
          borderRadius: 100,
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          '&.Mui-selected': {
            color: mode === 'light' ? 'primary.main' : indigo[200],
          },
        },
      },
    },
  };
};

const baseTheme = {
  palette: {
    primary: {
      main: '#3f51b5',
    },
    secondary: {
      main: '#f50057',
    },
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
      textTransform: undefined,
    },
  },
  spiff: {
    greyBorder: '1px solid #e0e0e0',
  },
};

export const createSpiffTheme = (mode: PaletteMode = 'light'): ThemeOptions => {
  return {
    ...baseTheme,
    palette: {
      mode,
      ...baseTheme.palette,
      ...customNotifications(mode),
    },
    components: {
      ...customComponents(mode),
    },
  };
};
