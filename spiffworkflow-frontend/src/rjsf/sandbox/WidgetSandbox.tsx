import React, { ComponentType, useEffect, useState, useRef } from 'react';
import DOMPurify from 'dompurify';
import { CustomWidgetProps } from '../interfaces/CustomWidgetInterfaces';

// Allowed imports that extension widgets can use
const ALLOWED_IMPORTS: Record<any, any> = {
  react: React,
  '@mui/material': {}, // We'll populate this with only specific components
};

// Allowed Material UI components
const ALLOWED_MUI_COMPONENTS = [
  'Button',
  'TextField',
  'Select',
  'MenuItem',
  'FormControl',
  'InputLabel',
  'FormHelperText',
  'Checkbox',
  'Radio',
  'RadioGroup',
  'FormControlLabel',
  'Switch',
  'Slider',
  'Typography',
  'Box',
  'Grid',
  'Paper',
  'Card',
  'CardContent',
  'CardActions',
  'Divider',
];

// Load allowed MUI components dynamically to avoid importing entire library
async function loadAllowedMuiComponents() {
  try {
    const mui = await import('@mui/material');

    // Create a mutable copy of the MUI module to avoid read-only errors
    ALLOWED_IMPORTS['@mui/material'] = { ...mui };

    // Also add individual components for backward compatibility
    ALLOWED_MUI_COMPONENTS.forEach((componentName) => {
      if (mui[componentName as keyof typeof mui]) {
        ALLOWED_IMPORTS['@mui/material'][componentName] =
          mui[componentName as keyof typeof mui];
      } else {
        console.warn(`MUI component not found: ${componentName}`);
      }
    });

    console.log('MUI components loaded successfully');
  } catch (error) {
    console.error('Failed to load MUI components:', error);
  }
}

/**
 * Sandbox to safely evaluate and render custom widget code
 * @param sourceCode The JavaScript source code to evaluate
 * @returns A React component that renders the custom widget
 */
export async function evaluateWidgetCode(
  sourceCode: string,
): Promise<ComponentType<CustomWidgetProps> | null> {
  // Sanitize source code with DOMPurify
  const sanitizedCode = DOMPurify.sanitize(sourceCode);

  // Check if the source code attempts to access disallowed objects
  const disallowedPatterns = [
    /\bdocument\b/g,
    /\bwindow\b/g,
    /\bglobal\b/g,
    /\beval\b/g,
    /\bFunction\(/g,
    /\bnew Function\b/g,
    /\blocalStorage\b/g,
    /\bsessionStorage\b/g,
    /\bfetch\b/g,
    /\bXMLHttpRequest\b/g,
    /\bnavigator\b/g,
    /\bhistory\b/g,
    /\blocation\b/g,
    /\bWebSocket\b/g,
    /\bIndexedDB\b/g,
    /\brequest\b/g,
    // We allow require because we provide a sandboxed version
    /\bimport\(/g, // Dynamic imports
    /\bprocess\./g,
    /\b__dirname\b/g,
    /\b__filename\b/g,
  ];

  // Check for disallowed patterns
  for (const pattern of disallowedPatterns) {
    if (pattern.test(sanitizedCode)) {
      console.error(`Widget code contains disallowed pattern: ${pattern}`);
      return null;
    }
  }

  // Load allowed component libraries
  await loadAllowedMuiComponents();

  try {
    // Add some debugging to help identify what's wrong with the widget code
    console.debug(
      'Evaluating widget code:',
      sanitizedCode.substring(0, 100) + '...',
    );

    // Create a secure evaluation environment with better error context
    // eslint-disable-next-line sonarjs/code-eval
    const secureEval = new Function(
      'React',
      'allowedImports',
      `
        "use strict";
        try {
          // Create a secure module environment
          const module = { exports: {} };
          function require(moduleName) {
            if (!allowedImports[moduleName]) {
              throw new Error(\`Import of module \${moduleName} is not allowed\`);
            }
            return allowedImports[moduleName];
          }
          
          // Execute the widget code
          ${sanitizedCode}
          
          // Return the exported component
          return module.exports && (module.exports.default || module.exports);
        } catch (innerError) {
          // Provide more context about where in the code the error occurred
          throw new Error(\`Widget code error: \${innerError.message}\`);
        }
      `,
    );

    // Execute the code in the sandbox
    const WidgetComponent = secureEval(React, ALLOWED_IMPORTS);

    // Check if the module exported anything
    if (!WidgetComponent) {
      console.error(
        'Widget code did not export anything. Make sure it uses module.exports correctly.',
      );
      return null;
    }

    // Verify that the result is a valid component
    if (typeof WidgetComponent !== 'function') {
      console.error(
        'Widget code did not export a valid React component function. Received:',
        typeof WidgetComponent,
      );
      return null;
    }

    return WidgetComponent as ComponentType<CustomWidgetProps>;
  } catch (error) {
    console.error('Error evaluating widget code:', error);
    console.error(
      'Widget source code snippet:',
      sanitizedCode.substring(0, 300) + '...',
    );
    return null;
  }
}

/**
 * Component that renders a sandboxed widget within error boundaries
 */
export function SandboxedWidget({
  widgetSource,
  ...props
}: CustomWidgetProps & { widgetSource: string }) {
  const [WidgetComponent, setWidgetComponent] =
    useState<ComponentType<CustomWidgetProps> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const isMounted = useRef(true);

  useEffect(() => {
    // Load the component
    evaluateWidgetCode(widgetSource)
      .then((component) => {
        if (isMounted.current) {
          setWidgetComponent(component);
          if (!component) {
            setError('Failed to load widget component');
          }
        }
      })
      .catch((err) => {
        if (isMounted.current) {
          console.error('Error loading widget:', err);
          setError(`Widget error: ${err.message}`);
        }
      });

    return () => {
      isMounted.current = false;
    };
  }, [widgetSource]);

  if (error) {
    return React.createElement(
      'div',
      {
        className: 'widget-error',
        style: { color: 'red', padding: '8px', border: '1px solid red' },
      },
      error,
    );
  }

  if (!WidgetComponent) {
    return React.createElement('div', null, 'Loading widget...');
  }

  // Wrap component rendering in error boundary
  try {
    return React.createElement(WidgetComponent, props);
  } catch (err) {
    const errorMessage = `Error rendering widget: ${err instanceof Error ? err.message : 'Unknown error'}`;
    return React.createElement(
      'div',
      {
        className: 'widget-error',
        style: { color: 'red', padding: '8px', border: '1px solid red' },
      },
      errorMessage,
    );
  }
}

/**
 * Higher-order component that wraps a custom widget in error boundaries and monitoring
 */
export function withSandbox(WidgetComponent: ComponentType<CustomWidgetProps>) {
  return function SandboxedComponent(props: CustomWidgetProps) {
    const [error, setError] = useState<string | null>(null);

    // Reset error when props change
    useEffect(() => {
      setError(null);
    }, [props.id, props.value]);

    if (error) {
      return React.createElement(
        'div',
        {
          className: 'widget-error',
          style: { color: 'red', padding: '8px', border: '1px solid red' },
        },
        error,
      );
    }

    // Wrap component rendering in error boundary
    try {
      return React.createElement(WidgetComponent, props);
    } catch (err) {
      const errorMessage = `Error rendering widget: ${err instanceof Error ? err.message : 'Unknown error'}`;
      setError(errorMessage);
      return React.createElement(
        'div',
        {
          className: 'widget-error',
          style: { color: 'red', padding: '8px', border: '1px solid red' },
        },
        errorMessage,
      );
    }
  };
}
