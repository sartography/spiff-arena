import { useEffect, useRef } from 'react';

interface DynamicCSSInjectionProps {
  cssContent: string;
  id: string;
}

/**
 * A component that injects CSS content into the document head.
 * This allows for dynamically loading CSS styles from extensions.
 *
 * @param cssContent - The CSS content to inject
 * @param id - A unique identifier for the style element
 */
function DynamicCSSInjection({ cssContent, id }: DynamicCSSInjectionProps) {
  const styleRef = useRef<HTMLStyleElement | null>(null);

  useEffect(() => {
    // Clean up any previous style element
    if (styleRef.current && document.head.contains(styleRef.current)) {
      document.head.removeChild(styleRef.current);
    }

    // Create and inject new style element
    const styleElement = document.createElement('style');
    styleElement.setAttribute('type', 'text/css');
    styleElement.setAttribute('id', `spiff-extension-css-${id}`);
    styleElement.textContent = cssContent;
    document.head.appendChild(styleElement);
    styleRef.current = styleElement;

    // Clean up on unmount
    return () => {
      if (styleRef.current && document.head.contains(styleRef.current)) {
        document.head.removeChild(styleRef.current);
        styleRef.current = null;
      }
    };
  }, [cssContent, id]);

  // This component doesn't render anything visible
  return null;
}

export default DynamicCSSInjection;
