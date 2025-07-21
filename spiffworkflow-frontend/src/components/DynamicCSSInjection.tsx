import { useEffect, useRef } from 'react';
// @ts-ignore - Ignoring TS1259 error about default import for DOMPurify
import DOMPurify from 'dompurify';

interface DynamicCSSInjectionProps {
  cssContent: string;
  id: string;
}

/**
 * A component that injects sanitized CSS content into the document head.
 * This allows for dynamically loading CSS styles from extensions.
 * CSS content is sanitized using DOMPurify to prevent CSS injection attacks.
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
    // Sanitize CSS content to prevent CSS injection attacks
    // DOMPurify supports CSS mode but TypeScript types don't reflect this
    const sanitizedCSS = DOMPurify.sanitize(cssContent, {
      FORBID_TAGS: ['style', 'link'],
      // @ts-expect-error - CSS profile is supported by DOMPurify but not in its TypeScript definition
      USE_PROFILES: { css: true },
    });
    styleElement.textContent = sanitizedCSS;
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
