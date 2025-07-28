# Custom Widget Extensions for SpiffWorkflow Forms

This document explains how to create and use custom form widgets in SpiffWorkflow extensions.

## Overview

Custom widgets allow you to extend the form capabilities of SpiffWorkflow by creating specialized input components. These widgets can be used in JSON Schema Forms to enhance the user experience, provide specialized inputs, or integrate with external systems.

Custom widgets are loaded from extension process models and are securely sandboxed to prevent security issues.

## Adding a Custom Widget to Your Extension

There are two ways to add custom widgets to your extension:

### 1. Using Extension UI Schema - Widgets Section (Recommended)

Add a `widgets` array to your `extension_uischema.json` file:

```json
{
  "version": "0.2",
  "pages": { ... },
  "ux_elements": [ ... ],
  "widgets": [
    {
      "name": "my-rating-widget",
      "file": "rating_widget.js",
      "metadata": {
        "displayName": "Rating Widget",
        "description": "A widget for rating with stars",
        "version": "1.0.0",
        "author": "Your Name"
      }
    }
  ]
}
```

### 2. Using UX Elements with Widget Display Location

Alternatively, you can use the UX Elements approach:

```json
{
  "version": "0.2",
  "pages": { ... },
  "ux_elements": [
    {
      "label": "My Rating Widget",
      "page": "/my-page",
      "display_location": "widget",
      "location_specific_configs": {
        "widget_file": "rating_widget.js",
        "widget_name": "my-rating-widget",
        "widget_metadata": {
          "displayName": "Rating Widget",
          "description": "A widget for rating with stars",
          "version": "1.0.0",
          "author": "Your Name"
        }
      }
    }
  ]
}
```

## Creating a Widget File

Widget files are JavaScript (.js) files that export a React component.

**Important**: 
- Files must use CommonJS module syntax with `module.exports` (not ES6 import/export)
- Use `require()` to import React and other libraries inside your component function, not at the top level
- Use `React.createElement()` instead of JSX syntax - JSX will cause errors
- Don't include external dependencies - use only allowed libraries (React, MUI)

Here's a basic template:

```javascript
// rating_widget.js
module.exports = {
  default: function RatingWidget(props) {
    var React = require('react');
    var mui = require('@mui/material');
    
    var id = props.id;
    var value = props.value;
    var onChange = props.onChange;
    var label = props.label;
    
    function handleChange(event, newValue) {
      onChange(newValue);
    }
    
    // IMPORTANT: Use React.createElement instead of JSX
    return React.createElement(
      mui.Box,
      null,
      [
        React.createElement(mui.Typography, { key: 'label' }, label),
        React.createElement(mui.Rating, { 
          key: 'rating',
          id: id, 
          value: value || 0,
          onChange: handleChange
        })
      ]
    );
  }
};
```

## Widget Props

Your widget will receive the following props:

| Prop | Type | Description |
|------|------|-------------|
| `id` | string | Unique identifier for the field |
| `value` | any | Current value of the field |
| `onChange` | function | Function to call when value changes |
| `schema` | object | JSON schema for this field |
| `uiSchema` | object | UI schema for this field |
| `label` | string | Field label |
| `required` | boolean | Whether field is required |
| `disabled` | boolean | Whether field is disabled |
| `readonly` | boolean | Whether field is read-only |
| `rawErrors` | string[] | Validation errors |
| `options` | object | Custom options from UI schema |

## Using the Widget in Forms

Once your widget is registered, you can use it in your form UI schema:

```json
{
  "ui:widget": "my-rating-widget",
  "ui:options": {
    "customOption1": "value1",
    "customOption2": "value2"
  }
}
```

The options specified in `ui:options` will be passed to your widget in the `options` prop.

## Security Restrictions

For security reasons, widgets run in a sandboxed environment with the following restrictions:

1. **Limited Access**: Widgets can't access browser APIs like `document`, `window`, `localStorage`, etc.
2. **Allowed Imports**: Only specific React, MUI, and Carbon components can be imported.
3. **No Network Access**: Direct network requests are not allowed.
4. **No Eval**: Dynamic code evaluation is prohibited.

### Allowed Import Libraries

- `react`: Core React functionality
- `@mui/material`: Selected Material UI components

## Allowed MUI Components

The following Material UI components are available:

- Button, TextField, Select, MenuItem
- FormControl, InputLabel, FormHelperText
- Checkbox, Radio, RadioGroup, FormControlLabel
- Switch, Slider, Typography, Box, Grid
- Paper, Card, CardContent, CardActions, Divider

## Example Widgets

### 1. Simple Rating Widget

```javascript
// Simple rating widget that doesn't use JSX syntax
// This is the recommended format for extension widgets

module.exports = {
  // IMPORTANT: Use a named function here, not an arrow function
  default: function SimpleRatingWidget(props) {
    // Get React from the sandbox environment
    var React = require('react');
    var useState = React.useState;

    // Extract props
    var id = props.id;
    var value = props.value;
    var onChange = props.onChange;
    var label = props.label;
    var required = props.required;

    // Import MUI components directly instead of destructuring
    // This ensures we get the actual components, not undefined
    var mui = require('@mui/material');
    var Box = mui.Box;
    var Typography = mui.Typography;
    var Rating = mui.Rating;

    // Default to 0 if value is undefined
    var currentValue = typeof value === 'number' ? value : 0;

    // Handle value change
    function handleChange(event, newValue) {
      onChange(newValue);
    }

    // Create elements individually and verify they exist
    if (!Box || !Typography || !Rating) {
      console.error('MUI components not available:', {
        Box: !!Box,
        Typography: !!Typography,
        Rating: !!Rating,
      });
      // Return a simple div if components aren't available
      return React.createElement(
        'div',
        null,
        'Error loading widget components',
      );
    }

    var labelElement = React.createElement(
      Typography,
      {
        key: 'label',
        component: 'legend',
        sx: { fontWeight: required ? 'bold' : 'normal' },
      },
      label + (required ? ' *' : ''),
    );

    var ratingElement = React.createElement(Rating, {
      key: 'rating',
      id: id,
      name: id,
      value: currentValue,
      onChange: handleChange,
    });

    return React.createElement(Box, { sx: { mb: 2, mt: 1 } }, [
      labelElement,
      ratingElement,
    ]);
  },
};
```

### 2. Autocomplete Widget

```javascript
// Example custom Autocomplete widget implementation
// This would be stored in a JavaScript file within the extension process model

module.exports = {
  /**
   * An autocomplete widget that fetches data from a specified API endpoint
   * This demonstrates more complex widget behavior with data fetching
   */
  default: function AutocompleteWidget(props) {
    var id = props.id;
    var value = props.value;
    var onChange = props.onChange;
    var label = props.label;
    var required = props.required;
    var disabled = props.disabled;
    var readonly = props.readonly;
    var rawErrors = props.rawErrors;
    var options = props.options;
    var React = require('react');
    var useState = React.useState;
    var useEffect = React.useEffect;
    var useRef = React.useRef;

    // MUI components
    var mui = require('@mui/material');

    // State for options, loading state, and input value
    var inputValueState = useState('');
    var inputValue = inputValueState[0];
    var setInputValue = inputValueState[1];
    var suggestionsState = useState([]);
    var suggestions = suggestionsState[0];
    var setSuggestions = suggestionsState[1];
    var loadingState = useState(false);
    var loading = loadingState[0];
    var setLoading = loadingState[1];
    var selectedOptionState = useState(null);
    var selectedOption = selectedOptionState[0];
    var setSelectedOption = selectedOptionState[1];
    var timeoutRef = useRef(null);

    // Configuration options with defaults
    var config = {
      minSearchLength: (options && options.minSearchLength) || 2,
      debounceMs: (options && options.debounceMs) || 300,
      labelField: (options && options.labelField) || 'label',
      valueField: (options && options.valueField) || 'value',
      // This is a mock endpoint - in a real widget, this would be configured via options
      apiEndpoint: (options && options.apiEndpoint) || '/api/autocomplete',
      placeholder: (options && options.placeholder) || 'Type to search...',
    };

    // Function to fetch suggestions
    var fetchSuggestions = function (searchText) {
      if (searchText.length < config.minSearchLength) {
        setSuggestions([]);
        return;
      }

      setLoading(true);

      // This is a mock implementation that simulates an API call
      // In a real widget, we would make an actual API call to the endpoint

      // Simulate API delay
      new Promise(function (resolve) {
        setTimeout(resolve, 500);
      })
        .then(function () {
          // Create some mock data based on the search term
          var mockData = [];
          var item1 = {};
          item1[config.valueField] = searchText + '-1';
          item1[config.labelField] = searchText + ' Option 1';
          mockData.push(item1);

          var item2 = {};
          item2[config.valueField] = searchText + '-2';
          item2[config.labelField] = searchText + ' Option 2';
          mockData.push(item2);

          var item3 = {};
          item3[config.valueField] = searchText + '-3';
          item3[config.labelField] = searchText + ' Option 3';
          mockData.push(item3);

          setSuggestions(mockData);
        })
        .catch(function (error) {
          console.error('Error fetching autocomplete suggestions:', error);
          setSuggestions([]);
        })
        .then(function () {
          setLoading(false);
        });
    };

    // Debounced search
    useEffect(
      function () {
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }

        timeoutRef.current = setTimeout(function () {
          fetchSuggestions(inputValue);
        }, config.debounceMs);

        return function () {
          if (timeoutRef.current) {
            clearTimeout(timeoutRef.current);
          }
        };
      },
      [inputValue],
    );

    // Update selectedOption when value changes from outside
    useEffect(
      function () {
        if (value) {
          // If value is an object with the expected structure
          if (typeof value === 'object' && value !== null) {
            setSelectedOption(value);
          }
          // If value is just the ID/value part
          else if (typeof value === 'string' || typeof value === 'number') {
            // Try to find in suggestions, or create a placeholder object
            var found = suggestions.find(function (item) {
              return item[config.valueField] === value;
            });
            if (found) {
              setSelectedOption(found);
            } else {
              // Create a placeholder with just the ID
              var placeholder = {};
              placeholder[config.valueField] = value;
              placeholder[config.labelField] = 'ID: ' + value;
              setSelectedOption(placeholder);

              // Optionally fetch the details for this ID
              // fetchItemDetails(value);
            }
          }
        } else {
          setSelectedOption(null);
        }
      },
      [value, suggestions],
    );

    // Check if there are validation errors
    var hasError = rawErrors && rawErrors.length > 0;

    // Create the renderInput function that would normally be passed as JSX
    var renderInput = function (params) {
      // Create the endAdornment with loading indicator if needed
      var loadingIndicator = loading
        ? React.createElement(mui.CircularProgress, {
            key: 'progress',
            color: 'inherit',
            size: 20,
          })
        : null;

      // Combine the loading indicator with the existing endAdornment
      var endAdornment = React.createElement(
        React.Fragment,
        null,
        [loadingIndicator, params.InputProps.endAdornment].filter(Boolean),
      );

      // Create the InputProps object
      var inputProps = Object.assign({}, params.InputProps, {
        endAdornment: endAdornment,
      });

      // Return the TextField
      return React.createElement(
        mui.TextField,
        Object.assign({}, params, {
          label: label,
          placeholder: config.placeholder,
          required: required,
          error: hasError,
          InputProps: inputProps,
        }),
      );
    };

    // Create error message if needed
    var errorMessage = hasError
      ? React.createElement(
          mui.FormHelperText,
          {
            key: 'error-message',
            error: true,
          },
          rawErrors.join(', '),
        )
      : null;

    // Create the Autocomplete component
    var autocomplete = React.createElement(mui.Autocomplete, {
      id: id,
      value: selectedOption,
      onChange: function (event, newValue) {
        setSelectedOption(newValue);
        onChange(newValue);
      },
      inputValue: inputValue,
      onInputChange: function (event, newInputValue) {
        setInputValue(newInputValue);
      },
      options: suggestions,
      getOptionLabel: function (option) {
        return option ? option[config.labelField] : '';
      },
      loading: loading,
      disabled: disabled || readonly,
      renderInput: renderInput,
    });

    // Return the final component wrapped in a Box
    return React.createElement(
      mui.Box,
      {
        sx: { mb: 2, mt: 1, width: '100%' },
      },
      [autocomplete, errorMessage].filter(Boolean),
    );
  },
};
```

## Best Practices

1. **Keep Widgets Focused**: Each widget should do one thing well.
2. **Handle Errors Gracefully**: Add error handling to avoid crashing the form.
3. **Support All Props**: Handle required, disabled, and readonly states.
4. **Show Validation**: Display rawErrors when provided.
5. **Default Values**: Always handle null/undefined values gracefully.
6. **Documentation**: Add comments to your code to explain how it works.

## Troubleshooting

If your widget doesn't appear or doesn't work as expected:

1. Check the browser console for errors
2. Verify that your widget file is properly referenced in the extension_uischema.json
3. Ensure your widget exports a default function or object
4. Check that you're not trying to use disallowed APIs
5. Verify that your UI schema correctly references the widget name

For more complex issues, look at the example widgets in `/src/rjsf/examples/` for guidance.
