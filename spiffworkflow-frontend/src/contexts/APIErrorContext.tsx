import React, { createContext, useState } from 'react';
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
  };
  const removeError = () => setError(null);

  const contextValue = React.useMemo(
    () => ({
      error,
      addError: (newError: ErrorForDisplay | null) => {
        addError(newError);
      },
      removeError: () => {
        removeError();
      },
    }),
    [error],
  );

  return (
    <APIErrorContext.Provider value={contextValue}>
      {children}
    </APIErrorContext.Provider>
  );
}
