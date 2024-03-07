import React from 'react';
import * as ReactDOMClient from 'react-dom/client';
import App from './App';

import './index.scss';
import './index.css';

import reportWebVitals from './reportWebVitals';

// @ts-expect-error TS(2345) FIXME: Argument of type 'HTMLElement | null' is not assig... Remove this comment to see the full error message
const root = ReactDOMClient.createRoot(document.getElementById('root'));

const doRender = () => {
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
};

doRender();

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
// @ts-expect-error TS(2554) FIXME: Expected 1 arguments, but got 0.
reportWebVitals();
