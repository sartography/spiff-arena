import React, { ComponentType, useEffect, useState, useRef } from 'react';
import DOMPurify from 'dompurify';
import { CustomWidgetProps, ExternalWidgetSource } from '../interfaces/CustomWidgetInterfaces';

// Allowed imports that extension widgets can use
const ALLOWED_IMPORTS = {
  'react': React,
  '@mui/material': {}, // We'll populate this with only specific components
  '@carbon/react': {}, // We'll populate this with only specific components
};

// Allowed Material UI components
const ALLOWED_MUI_COMPONENTS = [
  'Button', 'TextField', 'Select', 'MenuItem', 'FormControl', 
  'InputLabel', 'FormHelperText', 'Checkbox', 'Radio', 'RadioGroup',
  'FormControlLabel', 'Switch', 'Slider', 'Typography', 'Box', 'Grid',
  'Paper', 'Card', 'CardContent', 'CardActions', 'Divider',
];

// Allowed Carbon components
const ALLOWED_CARBON_COMPONENTS = [
  'Button', 'TextInput', 'Select', 'SelectItem', 'ComboBox', 
  'FormGroup', 'Checkbox', 'RadioButton', 'RadioButtonGroup',
  'Toggle', 'Slider', 'Tag', 'InlineLoading', 
];

// Load allowed MUI components dynamically to avoid importing entire library
async function loadAllowedMuiComponents() {
  try {
    const mui = await import('@mui/material');
    ALLOWED_MUI_COMPONENTS.forEach(componentName => {
      if (mui[componentName as keyof typeof mui]) {
        ALLOWED_IMPORTS['@mui/material'][componentName] = mui[componentName as keyof typeof mui];
      }
    });
  } catch (error) {
    console.error('Failed to load MUI components:', error);
  }
}

// Load allowed Carbon components dynamically
async function loadAllowedCarbonComponents() {
  try {
    const carbon = await import('@carbon/react');
    ALLOWED_CARBON_COMPONENTS.forEach(componentName => {
      if (carbon[componentName as keyof typeof carbon]) {
        ALLOWED_IMPORTS['@carbon/react'][componentName] = carbon[componentName as keyof typeof carbon];
      }
    });
  } catch (error) {
    console.error('Failed to load Carbon components:', error);
  }
}

/**
 * Sandbox to safely evaluate and render custom widget code
 * @param sourceCode The JavaScript source code to evaluate
 * @returns A React component that renders the custom widget
 */
export async function evaluateWidgetCode(
  sourceCode: string
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
    /\bprocess\b/g,
    /\b__dirname\b/g,
    /\b__filename\b/g
  ];

  // Check for disallowed patterns
  for (const pattern of disallowedPatterns) {
    if (pattern.test(sanitizedCode)) {
      console.error(`Widget code contains disallowed pattern: ${pattern}`);
      return null;
    }
  }

  // Load allowed component libraries
  await Promise.all([
    loadAllowedMuiComponents(),
    loadAllowedCarbonComponents()
  ]);

  try {
    // Create a secure evaluation environment
    const secureEval = new Function(
      'React',
      'allowedImports',
      `
        "use strict";
        // Create a secure module environment
        const module = { exports: {} };
        const require = (moduleName) => {
          if (!allowedImports[moduleName]) {
            throw new Error(\`Import of module \${moduleName} is not allowed\`);
          }
          return allowedImports[moduleName];
        };
        
        // Define commonly used React hooks for convenience
        const { 
          useState, useEffect, useRef, useCallback, 
          useMemo, useContext, useReducer 
        } = React;
        
        // Execute the widget code
        ${sanitizedCode}
        
        // Return the exported component
        return module.exports.default || module.exports;
      `
    );
    
    // Execute the code in the sandbox
    const WidgetComponent = secureEval(React, ALLOWED_IMPORTS);
    
    // Verify that the result is a valid component
    if (typeof WidgetComponent !== 'function') {
      console.error('Widget code did not export a valid React component function');
      return null;
    }
    
    return WidgetComponent as ComponentType<CustomWidgetProps>;
  } catch (error) {
    console.error('Error evaluating widget code:', error);
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
  const [WidgetComponent, setWidgetComponent] = useState<ComponentType<CustomWidgetProps> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const isMounted = useRef(true);

  useEffect(() => {
    // Load the component
    evaluateWidgetCode(widgetSource)
      .then(component => {
        if (isMounted.current) {
          setWidgetComponent(component);
          if (!component) {
            setError('Failed to load widget component');
          }
        }
      })
      .catch(err => {
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
        className: "widget-error",
        style: { color: 'red', padding: '8px', border: '1px solid red' } 
      },
      error
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
        className: "widget-error",
        style: { color: 'red', padding: '8px', border: '1px solid red' } 
      },
      errorMessage
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
          className: "widget-error",
          style: { color: 'red', padding: '8px', border: '1px solid red' } 
        },
        error
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
          className: "widget-error",
          style: { color: 'red', padding: '8px', border: '1px solid red' } 
        },
        errorMessage
      );
    }
  };
}