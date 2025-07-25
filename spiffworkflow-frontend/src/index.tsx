import React from 'react';
import * as ReactDOMClient from 'react-dom/client';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import App from './App';

import './index.scss';
import './index.css';
import './i18n';

// @ts-expect-error TS(2345) FIXME: Argument of type 'HTMLElement | null' is not assig... Remove this comment to see the full error message
const root = ReactDOMClient.createRoot(document.getElementById('root'));

/**
 * Creates an instance of the MUI theme that can be fed to the top-level ThemeProvider.
 * Nested ThemeProviders can be used to override specific components.
 * This override implements a tooltip that fits the overall app theme.
 */
const defaultTheme = createTheme();
const overrideTheme = createTheme({
  components: {
    MuiTooltip: {
      styleOverrides: {
        arrow: {
          '&::before': {
            color: '#F5F5F5',
            border: '1px solid grey',
          },
        },
        tooltip: {
          fontSize: '.8em',
          color: 'black',
          backgroundColor: '#F5F5F5',
          padding: '5px',
          border: '1px solid  grey',
        },
      },
    },
  },
});

const doRender = () => {
  root.render(
    <React.StrictMode>
      <ThemeProvider theme={defaultTheme}>
        <ThemeProvider theme={overrideTheme}>
          <App />
        </ThemeProvider>
      </ThemeProvider>
    </React.StrictMode>,
  );
};

doRender();
