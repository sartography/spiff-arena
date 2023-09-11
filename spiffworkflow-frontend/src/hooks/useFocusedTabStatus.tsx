import { useEffect, useState } from 'react';

export function useFocusedTabStatus() {
  // eslint-disable-next-line no-undef
  const [isFocused, setIsFocused] = useState(true);

  useEffect(() => {
    function handleFocus() {
      setIsFocused(true);
    }
    function handleBlur() {
      setIsFocused(false);
    }

    window.addEventListener('focus', handleFocus);
    window.addEventListener('blur', handleBlur);
    // Calls onFocus when the window first loads
    handleFocus();
    // Specify how to clean up after this effect:
    return () => {
      window.removeEventListener('focus', handleFocus);
      window.removeEventListener('blur', handleBlur);
    };
  }, []);

  return isFocused;
}
