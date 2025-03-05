// src/common/hooks/useAPIError/index.js
import { useContext } from 'react';
// Import MUI components if needed
// import { SomeMUIComponent } from '@mui/material';
import { APIErrorContext } from '../contexts/APIErrorContext';

function useAPIError() {
  const { error, addError, removeError } = useContext(APIErrorContext);
  return { error, addError, removeError };
}

export default useAPIError;
