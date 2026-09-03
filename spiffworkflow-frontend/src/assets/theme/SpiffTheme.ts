import { PaletteMode, ThemeOptions } from '@mui/material';
import {
  blue,
  blueGrey,
  green,
  grey,
  lightBlue,
  orange,
  red,
  yellow,
} from '@mui/material/colors';

// Kept for reference / an easy revert, not currently used -- see BRAND
// below. Exported (rather than a plain unused local) so lint doesn't flag
// it as dead code.
export const BRAND_GREEN = {
  light: {
    main: '#15803D',
    light: '#16A34A',
    dark: '#166534',
  },
  dark: {
    main: '#158740',
    light: '#16A34A',
    dark: '#166534',
    // Brighter accent for content that needs to stand out against dark
    // backgrounds more than `main` allows (e.g. the selected-tab indicator).
    accent: '#86EFAC',
  },
};

// WCAG 2.1 AA (4.5:1 for normal text):
// - light.main #0F766E: 5.47:1 vs white, 5.02:1 vs #f5f5f5 (as text), and
//   5.47:1 for white text on it as a filled background -- one shade clears
//   both directions on a light background, so light mode keeps white
//   contrastText.
// - dark.main #14B8A6 has to work in three places: as text/border directly
//   on the page background (e.g. outlined buttons -- 7.53:1 vs #121212),
//   as the selected-nav-item text against SideNav's lighter
//   selected-row highlight background (rgba(255,255,255,0.16) over
//   #121212, ~#383838 -- 4.71:1), and as a filled-button background
//   (8.44:1 for BLACK text on it -- it's too light for legible white text,
//   so dark mode's contrastText, in baseTheme below, is black instead).
//   One shade clearing all three, rather than trying to force a single
//   shade+contrastText to do it (which cannot work on a dark background --
//   see BRAND_GREEN's dark.main for the earlier, narrower version of this
//   that only checked two of the three and got the tradeoff wrong).
const BRAND_TEAL = {
  light: {
    main: '#0F766E',
    light: '#0D9488',
    dark: '#134E4A',
  },
  dark: {
    main: '#14B8A6',
    light: '#2DD4BF',
    dark: '#0D9488',
    // Brighter accent for content that needs to stand out against dark
    // backgrounds more than `main` allows (e.g. the selected-tab indicator).
    accent: '#5EEAD4',
  },
};

const BRAND = BRAND_TEAL;

/**
 * Global palette tokens.
 * Remember, all light mode properties have to be reflected in the dark mode object
 */
const customPalette = (mode: PaletteMode) => {
  const lightModeColors = {
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
      bluegreydark: blueGrey[200],
      bluegreylight: blueGrey[50],
      bluegreymedium: blueGrey[100],
      dark: grey[500],
      darker: grey[700],
      default: grey[50],
      light: grey[100],
      medium: grey[300],
      mediumdark: grey[400],
      mediumlight: grey[200],
      nav: '#ffffff',
      offblack: grey[900],
      paper: '#ffffff',
    },
    text: {
      primary: grey[900],
      secondary: grey[800],
      disabled: grey[400],
      subheading: grey[600],
      accent: yellow[900], // see also spotColors.goldStar
    },
    borders: {
      table: '#e7ebed',
      primary: grey[400],
      secondary: grey[600],
    },
    spotColors: {
      goldStar: yellow[700],
      selectedBackground: lightBlue[100],
      linkHover: lightBlue[700],
    },
  };
  const darkModeColors = {
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
      bluegreydark: blueGrey[900],
      bluegreylight: blueGrey[800],
      bluegreymedium: blueGrey[700],
      dark: grey[700],
      darker: grey[900],
      light: 'rgba(255, 255, 255, 0.16)',
      medium: grey[700],
      mediumdark: grey[600],
      mediumlight: grey[800],
      nav: '#121212',
      offblack: grey[100],
      default: '#121212',
    },
    text: {
      primary: grey[100],
      secondary: grey[200],
      disabled: grey[600],
      subheading: grey[400],
      accent: yellow[700], // see also spotColors.goldStar
    },
    borders: {
      table: grey[800],
      primary: grey[800],
      secondary: BRAND.dark.dark,
    },
    spotColors: {
      goldStar: yellow[700],
      selectedBackground: blueGrey[500],
      linkHover: lightBlue[200],
    },
  };

  return mode === 'light' ? lightModeColors : darkModeColors;
};

/** Global component-specific overrides */
const customComponents = (mode: PaletteMode) => {
  const brand = mode === 'light' ? BRAND.light : BRAND.dark;
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
          // MUI dims inactive tabs via opacity on the inherited text color by
          // default, which fails WCAG 2.1 AA color-contrast against our light
          // backgrounds. Use the theme's own (already contrast-checked)
          // secondary text color at full opacity instead.
          opacity: 1,
          color: mode === 'light' ? grey[800] : grey[200],
          '&.Mui-selected': {
            color: mode === 'light' ? brand.main : BRAND.dark.accent,
          },
        },
      },
    },
    // Plain <a> tags (e.g. react-router's <Link>, which renders unstyled)
    // otherwise fall back to the browser default blue instead of the brand
    // color. This is a zero-specificity DEFAULT, not an override: :where()
    // means it never competes with any component's own color (e.g.
    // SideNav's selected/unselected logic) no matter how that color was
    // set (sx, inherit, a plain style prop) -- it only fills in for
    // elements that have no color opinion of their own.
    MuiCssBaseline: {
      styleOverrides: {
        ':where(a)': {
          color: brand.main,
        },
        ':where(a:visited)': {
          color: brand.main,
        },
        ':where(a:hover)': {
          color: brand.dark,
        },
      },
    },
    MuiTooltip: {
      styleOverrides: {
        arrow: {
          '&::before': {
            color: mode === 'light' ? grey[100] : grey[800],
            border: `1px solid ${mode === 'light' ? grey[500] : grey[600]}`,
          },
        },
        tooltip: {
          fontSize: '.8em',
          color: mode === 'light' ? grey[900] : grey[100],
          backgroundColor: mode === 'light' ? grey[100] : grey[800],
          padding: '5px',
          border: `1px solid ${mode === 'light' ? grey[500] : grey[600]}`,
        },
      },
    },
  };
};

/** Base, used by all core MUI components */
const baseTheme = (mode: PaletteMode) => {
  const typographyOptions = {
    button: {
      textTransform: undefined,
    },
    h1: {
      fontSize: '2rem', // 32px, down from 6rem default, since even 3rem felt big
    },
    h2: {
      fontSize: '1.875rem', // 30px, unchanged
    },
    h3: {
      fontSize: '1.5rem', // 24px, unchanged
    },
    h4: {
      fontSize: '1.0625rem', // 17px, unchanged
    },
    h5: {
      fontSize: '0.75rem', // 12px, unchanged
    },
    h6: {
      fontSize: '0.625rem', // 10px, unchanged
    },
  };

  const lightModeColors = {
    palette: {
      primary: {
        ...BRAND.light,
        contrastText: '#ffffff',
      },
      secondary: {
        main: '#ffffff',
        contrastText: '#000000',
      },
    },
    typography: typographyOptions,
  };

  const darkModeColors = {
    palette: {
      primary: {
        main: BRAND.dark.main,
        light: BRAND.dark.light,
        dark: BRAND.dark.dark,
        // BRAND.dark.main is chosen to pass contrast as text/border against
        // the dark background (and the selected-nav-item highlight), which
        // makes it too light for legible WHITE text as a filled button
        // background -- black text passes instead (8.44:1). See the
        // comment on BRAND_TEAL.dark above.
        contrastText: '#000000',
      },
      secondary: {
        main: grey[300],
        contrastText: '#000000',
      },
    },
    typography: typographyOptions,
  };
  return mode === 'light' ? lightModeColors : darkModeColors;
};

/** Compose custom palette, components and base them into MUI ThemeOptions object. */
export const createSpiffTheme = (mode: PaletteMode = 'light'): ThemeOptions => {
  return {
    ...baseTheme(mode),
    palette: {
      mode,
      ...baseTheme(mode).palette,
      ...customPalette(mode),
    },
    components: {
      ...customComponents(mode),
    },
  };
};
