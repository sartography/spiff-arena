import React from 'react';
import * as ReactDOMClient from 'react-dom/client';
import { createTheme, PaletteMode, ThemeProvider } from '@mui/material/styles';
import App from './App';
import { createSpiffTheme } from './assets/theme/SpiffTheme';

import './index.css';
import './i18n';

// @ts-expect-error TS(2345) FIXME: Argument of type 'HTMLElement | null' is not assig... Remove this comment to see the full error message
const root = ReactDOMClient.createRoot(document.getElementById('root'));

const storedTheme = (localStorage.getItem('theme') || 'light') as PaletteMode;
const defaultTheme = createTheme(createSpiffTheme(storedTheme));

const doRender = () => {
  root.render(
    <React.StrictMode>
      <ThemeProvider theme={defaultTheme}>
        <App />
      </ThemeProvider>
    </React.StrictMode>,
  );
};

doRender();
