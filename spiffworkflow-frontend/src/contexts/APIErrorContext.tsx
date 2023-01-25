import React, { createContext, useState, useCallback } from 'react';
import { ErrorForDisplay } from '../interfaces';

type ErrorContextType = {
  error: null | ErrorForDisplay;
  addError: Function;
  removeError: Function;
};
export const APIErrorContext = createContext<ErrorContextType>({
  error: null,
  // eslint-disable-next-line no-unused-vars
  addError: () => {},
  removeError: () => {},
});

// @ts-ignore
// eslint-disable-next-line react/prop-types
export default function APIErrorProvider({ children }) {
  const [error, setError] = useState<ErrorForDisplay | null>(null);
  const addError = (errorForDisplay: ErrorForDisplay | null) => {
    setError(errorForDisplay);
    console.log('Adding an error.', errorForDisplay);
  }
  const removeError = () => setError(null);

  const contextValue = {
    error,
    addError: useCallback(
      (newError: ErrorForDisplay | null) => addError(newError),
      []
    ),
    removeError: useCallback(() => removeError(), []),
  };

  return (
    <APIErrorContext.Provider value={contextValue}>
      {children}
    </APIErrorContext.Provider>
  );
}
