import { PaletteMode, ThemeOptions } from '@mui/material';
import {
  blue,
  cyan,
  green,
  indigo,
  orange,
  pink,
  red,
} from '@mui/material/colors';

const customNotifications = (mode: PaletteMode) => {
  return mode === 'light'
    ? {
        success: {
          main: green[300],
          light: green[100],
          dark: green[500],
        },
        warning: {
          main: orange[300],
          light: orange[100],
          dark: orange[500],
        },
        error: {
          main: red[300],
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
          main: orange[500],
          light: orange[300],
          dark: orange[700],
          contrastText: '#fff',
        },
        error: {
          main: red[500],
          light: red[300],
          dark: red[700],
          contrastText: '#fff',
        },
        info: {
          main: blue[500],
          light: blue[300],
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
          borderRadius: 8,
          maxHeight: 40,
          color: 'primary',
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          '&.Mui-selected': {
            color: mode === 'light' ? 'primary.main' : cyan[200],
          },
        },
      },
    },
  };
};

const baseTheme = {
  palette: {
    primary: {
      main: cyan[800],
      light: cyan[600],
      dark: cyan[900],
      contrastText: '#ffffff',
    },
    secondary: {
      main: pink.A100,
    },
  },
  typography: {
    button: {
      textTransform: undefined,
    },
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
