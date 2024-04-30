import { ThemeOptions } from '@mui/material';

export const globalTheme: ThemeOptions = {
  palette: {
    primary: { main: '#6750A4' },
    secondary: { main: '#625B71' },
  },
  typography: {
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
    // Name of the component
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
