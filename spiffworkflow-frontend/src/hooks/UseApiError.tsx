// src/common/hooks/useAPIError/index.js
import { useContext } from 'react';
import { APIErrorContext } from '../contexts/APIErrorContext';

function useAPIError() {
  const { error, addError, removeError } = useContext(APIErrorContext);
  return { error, addError, removeError };
}

export default useAPIError;
