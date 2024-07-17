import { PaletteMode, ThemeOptions } from '@mui/material';
import {
  blue,
  blueGrey,
  cyan,
  green,
  grey,
  lightBlue,
  orange,
  red,
  yellow,
} from '@mui/material/colors';

/**
 * Global palette tokens.
 * Remember, all light mode properties have to be reflected in the dark mode object
 */
const customPalette = (mode: PaletteMode) => {
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
        background: {
          paper: grey[100],
          default: grey.A100,
          light: grey[100],
          mediumlight: grey[200],
          medium: grey[300],
          mediumdark: grey[400],
          dark: grey[500],
          darker: grey[700],
          offblack: grey[900],
          bluegreylight: blueGrey[50],
          bluegreymedium: blueGrey[100],
          bluegreydark: blueGrey[200],
        },
        text: {
          primary: grey[900],
          secondary: grey[800],
          disabled: grey[400],
          subheading: grey[600],
        },
        borders: {
          primary: grey[400],
          seconday: grey[600],
        },
        spotColors: {
          goldStar: yellow[700],
          selectedBackground: lightBlue[100],
          linkHover: lightBlue[700],
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
        background: {
          paper: '#121212',
          default: '#121212',
          bluegreymedium: blueGrey[600],
        },
        text: {
          primary: grey[100],
          secondary: grey[200],
          disabled: grey[600],
          subheading: grey[400],
        },
        borders: {
          primary: grey[800],
          seconday: cyan[800],
        },
        spotColors: {
          goldStar: yellow[700],
          selectedBackground: blueGrey[500],
        },
      };
};

/** Global component-specific overrides */
const customComponents = (mode: PaletteMode) => {
  // We wanted rounded buttons everywhere
  return {
    MuiButton: {
      styleOverrides: {
        root: {
          fontSize: '14px',
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

/** Base, used by all core MUI components */
const baseTheme = {
  palette: {
    primary: {
      main: cyan[600],
      light: cyan[400],
      dark: cyan[800],
      contrastText: '#ffffff',
    },
  },
  typography: {
    button: {
      textTransform: undefined,
    },
  },
};

/** Compose custom palette, components and base them into MUI ThemeOptions object. */
export const createSpiffTheme = (mode: PaletteMode = 'light'): ThemeOptions => {
  return {
    ...baseTheme,
    palette: {
      mode,
      ...baseTheme.palette,
      ...customPalette(mode),
    },
    components: {
      ...customComponents(mode),
    },
  };
};
