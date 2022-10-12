import { createContext } from 'react';

// @ts-expect-error TS(2554) FIXME: Expected 1 arguments, but got 0.
const ErrorContext = createContext();
export default ErrorContext;
